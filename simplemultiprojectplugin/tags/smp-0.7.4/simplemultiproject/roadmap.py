# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2021 Cinc
#
# License: 3-clause BSD
#
from pkg_resources import get_distribution, parse_version, resource_filename
from simplemultiproject.api import IRoadmapDataProvider
from simplemultiproject.compat import JTransformer
from simplemultiproject.model import Project
from simplemultiproject.permission import PERM_TEMPLATE, SmpPermissionPolicy
from simplemultiproject.session import get_project_filter_settings, \
    get_filter_settings
from simplemultiproject.smp_model import SmpMilestone, SmpVersion
from trac.config import OrderedExtensionsOption
from trac.core import *
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, Chrome, ITemplateProvider


__all__ = ['SmpRoadmapModule']


class SmpRoadmapModule(Component):
    """Manage roadmap page for projects.

    This component allows to filter roadmap entries by project. It is possible to group entries by project.
    """

    implements(IRequestFilter, IRoadmapDataProvider, ITemplateProvider)

    data_provider = OrderedExtensionsOption(
        'simple-multi-project', 'roadmap_data_provider', IRoadmapDataProvider,
        default="",
        doc="""Specify the order of plugins providing data for roadmap page""")

    data_filters = OrderedExtensionsOption(
        'simple-multi-project', 'roadmap_data_filters', IRoadmapDataProvider,
        default="",
        doc="""Specify the order of plugins filtering data for roadmap page""")

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')
    group_tmpl = None

    def __init__(self):
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_version = SmpVersion(self.env)

    def _load_template(self):
        chrome = Chrome(self.env)
        if self.pre_1_3:
            self.group_tmpl = chrome.load_template("smp_roadmap.html", None)
        else:
            self.group_tmpl = chrome.load_template("smp_roadmap_jinja.html", False)

    # Unused preference item
    # if get_filter_settings(req, 'roadmap', 'smp_hideprojdesc'):
    #     hide.append('projectdescription')
    # prefs = """<div>
    #               <input type="checkbox" id="hideprojectdescription" name="smp_hideprojdesc" value="1"
    #                      {hideprjdescchk} />
    #               <label for="hideprojectdescription">{hideprjdesclabel}</label>
    #         </div>"""

    def create_hide_milestone_item(self, req):
        prefs = """
        <div>
              <input type="checkbox" id="hidemilestones" name="smp_hidemilestones" value="1"
                     {hidemschk} />
              <label for="hidemilestones">{hidemslabel}</label>
        </div>"""
        hidemschk = ' checked="checked"' if get_filter_settings(req, 'roadmap', 'smp_hidemilestones') else '',
        return prefs.format(hidemslabel=_('Hide milestones'), hidemschk=hidemschk)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        """Call extensions adding data or filtering data in the
        appropriate order.
        """
        if data:
            path_elms = req.path_info.split('/')
            if len(path_elms) > 1 and path_elms[1] == 'roadmap':
                add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")

                for provider in self.data_provider:
                    data = provider.add_data(req, data)

                for provider in self.data_filters:
                    data = provider.filter_data(req, data)

                # Add project table to preferences on roadmap page
                # xpath: //form[@id="prefs"]
                xform = JTransformer('form#prefs')
                filter_list = [xform.prepend(create_proj_table(self, req, 'roadmap'))]

                # Add 'group' check box
                group_proj = get_filter_settings(req, 'roadmap', 'smp_group')
                chked = ' checked="1"' if group_proj else ''
                # xpath: //form[@id="prefs"]
                xform = JTransformer('form#prefs')
                filter_list.append(xform.prepend(u'<div>'
                                                 u'<input type="hidden" name="smp_update" value="group" />'
                                                 u'<input type="checkbox" id="groupbyproject" name="smp_group" '
                                                 u'value="1"%s/>'
                                                 u'<label for="groupbyproject">Group by project</label></div><br />' %
                                                 chked))
                # Add preference checkbox
                xform = JTransformer('#prefs div.buttons')
                filter_list.append(xform.before(self.create_hide_milestone_item(req)))

                if chked:
                    if not self.group_tmpl:
                        self._load_template()
                    # Add new grouped content
                    # xpath: //div[@class="milestones"]
                    xform = JTransformer('div.milestones')
                    chrome = Chrome(self.env)
                    data = chrome.populate_data(req, data)
                    if self.pre_1_3:
                        filter_list.append(xform.before(self.group_tmpl.generate(**data).render('html')))
                    else:
                        filter_list.append(xform.before(chrome.render_template_string(self.group_tmpl, data)))
                    filter_list.append(xform.remove())  # Remove default milestone entries

                add_script_data(req, {'smp_filter': filter_list})
                add_script(req, 'simplemultiproject/js/jtransform.js')

        return template, data, content_type

    # IRoadmapDataProvider

    def add_projects_to_dict(self, req, data):
        """Add allowed projects to the data dict.

        :param req: a Request object
        :param data: dictionary holding data for template
        :return None

        This checks if the user has access to the projects. If not a project won't be added to the list of available
        projects. Closed projects are ignored, too.
        """
        usr_projects = SmpPermissionPolicy.active_projects_by_permission(req, Project.select(self.env))
        data.update({'projects': usr_projects,
                     'project_ids': [project.id for project in usr_projects]})

    def add_project_info_to_milestones(self, data):
        # Do the milestone updates
        data['ms_without_prj'] = False
        if data.get('milestones'):
            # Add info about linked projects
            for item in data.get('milestones'):
                # Used in smp_roadmap.html to check if there is a ms - proj link
                ids_for_ms = self.smp_milestone.get_project_ids_for_resource_item('milestone', item.name)
                if not ids_for_ms:
                    item.id_project = []  # Milestones without a project are for all
                    data['ms_without_prj'] = True
                else:
                    item.id_project = ids_for_ms

    def add_data(self, req, data):
        # Get all projects user has access to.
        self.add_projects_to_dict(req, data)
        self.add_project_info_to_milestones(data)
        # self.add_project_info_to_versions(data)

        return data

    def filter_data(self, req, data):

        if data and get_filter_settings(req, 'roadmap', 'smp_hidemilestones'):
            data['milestones'] = []
            data['milestone_stats'] = []

        filter_proj = get_project_filter_settings(req, 'roadmap', 'smp_projects', 'All')
        if 'All' in filter_proj:
            return data

        # Remove projects from dict which are not selected. The template will loop over this data.
        if 'projects' in data:
            filtered = []
            for project in data['projects']:
                if project.name in filter_proj:
                    filtered.append(project)
            data['projects'] = filtered

        if 'milestones' in data:
            item_stats = data.get('milestone_stats')
            filtered_items = []
            filtered_item_stats = []
            for idx, ms in enumerate(data['milestones']):
                ms_proj = self.smp_milestone.get_project_names_for_item(ms.name)
                # Milestones without linked projects are good for every project
                if not ms_proj:
                    filtered_items.append(ms)
                    filtered_item_stats.append(item_stats[idx])
                else:
                    # List of project names
                    for name in ms_proj:
                        if name in filter_proj:
                            filtered_items.append(ms)
                            filtered_item_stats.append(item_stats[idx])
                            break  # Only add a milestone once
            data['milestones'] = filtered_items
            data['milestone_stats'] = filtered_item_stats

        # TODO: Is this still needed?
        if 'versions' in data:
            item_stats = data.get('version_stats')
            filtered_items = []
            filtered_item_stats = []
            for idx, ms in enumerate(data['versions']):
                ms_proj = self.smp_version.get_project_names_for_item(ms.name)
                # Versions without linked projects are good for every project
                if not ms_proj:
                    filtered_items.append(ms)
                    filtered_item_stats.append(item_stats[idx])
                else:
                    # List of project names
                    for name in ms_proj:
                        if name in filter_proj:
                            filtered_items.append(ms)
                            filtered_item_stats.append(item_stats[idx])
                            break  # Only add a version once

            data['versions'] = filtered_items
            data['version_stats'] = filtered_item_stats

        return data

    # ITemplateProvider methods

    def get_templates_dirs(self):
        self.log.info(resource_filename(__name__, 'templates'))
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]


def div_from_projects(all_projects, filter_prj, size):
    """Create the project select div for the preference pane on Roadmap and timeline page."""
    # Don't change indentation here without fixing the test cases
    div_templ = u"""<div style="overflow:hidden;">
<div>
<label>Filter Project:</label>
</div>
<div>
<input type="hidden" name="smp_update" value="filter">
<select id="Filter-Projects" name="smp_projects" multiple size="{size}" style="overflow:auto;">
    <option value="All"{all_selected}>All</option>
    {options}
</select>
</div>
<br>
</div>"""
    option_tmpl = u"""<option value="{p_name}"{sel}>
        {p_name}
    </option>"""

    options = u""
    for item in all_projects:
        sel = u' selected' if item.name in filter_prj else u''
        options += option_tmpl.format(p_name=item.name, sel=sel)

    return div_templ.format(size=size, all_selected='' if filter_prj else u' selected', options=options)


def create_proj_table(self, req, session_name='roadmap'):
    """Create a select tag holding valid projects (means not closed) for
    the current user.

    @param self: Component instance holding the Environment object
    @param req      : Trac request object

    @return DIV tag holding a project select control with label
    """
    projects = Project.select(self.env)
    filtered_projects = SmpPermissionPolicy.active_projects_by_permission(req, projects)

    if filtered_projects:
        size = len(filtered_projects) + 1  # Account for 'All' option
    else:
        return u'<div><p>No projects defined.</p><br></div>'

    if size > 5:
        size = 5

    # list of currently selected projects. The info is stored in the request or session data
    filter_prj = get_project_filter_settings(req, session_name, 'smp_projects', 'All')
    if 'All' in filter_prj:
        filter_prj = []

    return div_from_projects(filtered_projects, filter_prj, size)
