# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Cinc
#
# License: 3-clause BSD
#
from genshi.filters import Transformer
from trac.config import OrderedExtensionsOption
from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, Chrome

from simplemultiproject.api import IRoadmapDataProvider
from simplemultiproject.compat import JTransformer
from simplemultiproject.model import Project
from simplemultiproject.permission import PERM_TEMPLATE, SmpPermissionPolicy
from simplemultiproject.session import get_project_filter_settings, \
    get_filter_settings
from simplemultiproject.smp_model import SmpMilestone, SmpProject, SmpVersion

__all__ = ['SmpRoadmapModule']


class SmpRoadmapModule(Component):
    """Manage roadmap page for projects.

    This component allows to filter roadmap entries by project. It is possible to group entries by project.
    """

    implements(IRequestFilter, IRoadmapDataProvider, ITemplateStreamFilter)

    data_provider = OrderedExtensionsOption(
        'simple-multi-project', 'roadmap_data_provider', IRoadmapDataProvider,
        default="",
        doc="""Specify the order of plugins providing data for roadmap page""")

    data_filters = OrderedExtensionsOption(
        'simple-multi-project', 'roadmap_data_filters', IRoadmapDataProvider,
        default="",
        doc="""Specify the order of plugins filtering data for roadmap page""")

    def __init__(self):
        chrome = Chrome(self.env)
        self.group_tmpl = chrome.load_template("smp_roadmap.html", None)
        self.smp_project = SmpProject(self.env)  # For create_projects_table
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_version = SmpVersion(self.env)

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
                # ITemplateProvider is implemented in another component
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

                # Change label to include versions
                # xpath: //label[@for="showcompleted"]
                # xform = JTransformer('label[for=showcompleted]')
                # filter_list.append(xform.replace(u'<label for="showcompleted">Show completed milestones</label>'))

                add_script_data(req, {'smp_filter': filter_list})
                add_script(req, 'simplemultiproject/js/jtransform.js')

                data.update({'show': req.args.get('show', [])  # TODO: is this used at all?
                             })

        return template, data, content_type

    # IRoadmapDataProvider

    def add_projects_to_dict(self, req, data):
        """Add allowed projects to the data dict.

        This checks if the user has access to a project. If not the project won't be added.
        """
        # Get all projects user has access to.
        usr_projects = []
        for project in Project.select(self.env):  # This is already sorted by name
            if project.restricted:
                if (PERM_TEMPLATE % project.id) in req.perm:
                    usr_projects.append(project)
            else:
                usr_projects.append(project)
        all_known_proj_ids = [project.id for project in usr_projects]

        data.update({'projects': usr_projects,
                     'project_ids': all_known_proj_ids})

    def add_project_info_to_milestones(self, data):
        # Do the milestone updates
        if data.get('milestones'):
            all_known_proj_ids = data['project_ids']
            # Add info about linked projects
            for item in data.get('milestones'):
                ids_for_ms = self.smp_milestone.get_project_ids_for_resource_item('milestone', item.name)
                if not ids_for_ms:
                    # Used in smp_roadmap.html to check if there is a ms - proj link
                    item.id_project = all_known_proj_ids  # Milestones without a project are for all
                else:
                    item.id_project = ids_for_ms

    def add_project_info_to_versions(self, data):
        if data.get('versions'):
            all_known_proj_ids = data['project_ids']
            for item in data.get('versions'):
                ids_for_ver = self.smp_version.get_project_ids_for_resource_item('version', item.name)
                if not ids_for_ver:
                    # Used in smp_roadmap.html to check if there is a version - proj link
                    item.id_project = all_known_proj_ids  # Versions without a project are for all
                else:
                    item.id_project = ids_for_ver

    def add_data(self, req, data):
        # Get all projects user has access to.
        self.add_projects_to_dict(req, data)
        self.add_project_info_to_milestones(data)
        self.add_project_info_to_versions(data)

        return data

    def filter_data(self, req, data):

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
                            break  # Only add a milstone once
            data['milestones'] = filtered_items
            data['milestone_stats'] = filtered_item_stats

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

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'roadmap.html':

            group_proj = get_filter_settings(req, 'roadmap', 'smp_group')
            chked = ''
            if group_proj:
                chked = 'checked="1"'
            if chked:
                filter_ = Transformer('//div[@class="milestones"]')
                # Add new grouped content
                stream |= filter_.before(self.group_tmpl.generate(**data))
                # Remove old milestone contents
                stream |= filter_.remove()
        return stream


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
