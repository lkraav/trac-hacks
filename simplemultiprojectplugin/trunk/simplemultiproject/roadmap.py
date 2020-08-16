# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Cinc
#
# License: 3-clause BSD
#

from genshi.template import MarkupTemplate
from genshi import HTML
from genshi.filters import Transformer
from trac.config import OrderedExtensionsOption
from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, Chrome

from simplemultiproject.smp_model import SmpMilestone, SmpProject, SmpVersion
from simplemultiproject.api import IRoadmapDataProvider
from simplemultiproject.permission import PERM_TEMPLATE, SmpPermissionPolicy
from simplemultiproject.session import get_project_filter_settings, \
    get_filter_settings

__all__ = ['SmpRoadmapGroup', 'SmpRoadmapProjectFilter', 'SmpRoadmapModule']


class SmpRoadmapGroup(Component):
    """Milestone and version grouping by project"""

    implements(IRequestFilter, ITemplateStreamFilter, IRoadmapDataProvider)

    def __init__(self):
        chrome = Chrome(self.env)
        self.group_tmpl = chrome.load_template("smp_roadmap.html", None)
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_project = SmpProject(self.env)
        self.smp_version = SmpVersion(self.env)

    # IRoadmapDataProvider

    def add_data(self, req, data):
        group_proj = get_filter_settings(req, 'roadmap', 'smp_group')
        if group_proj:
            data['smp_groupproject'] = True
        return data

    def filter_data(self, req, data):
        return data

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        path_elms = req.path_info.split('/')
        if data and len(path_elms) > 1 and path_elms[1] == 'roadmap':
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")

            # TODO: this stuff probably should be in filter_data()
            # Get all projects user has access to.
            usr_projects = []
            for project in self.smp_project.get_all_projects():  # This is already sorted by name
                if project.restricted:
                    if (PERM_TEMPLATE % project.id) in req.perm:
                        usr_projects.append(project)
                else:
                    usr_projects.append(project)
            all_known_proj_ids = [project.id for project in usr_projects]

            # Get list of project ids linked to any milestone. Note this list may have duplicates
            ms_project_ids = [id_p for ms, id_p in self.smp_milestone.get_all_milestones_and_id_project_id()]
            # Get list of project ids linked to any version. Note this list may have duplicates
            vers_project_ids = [id_p for v, id_p in self.smp_version.get_all_versions_and_project_id()]

            # Do the milestone updates
            if data.get('milestones'):
                # Add info about linked projects
                for item in data.get('milestones'):
                    ids_for_ms = self.smp_milestone.get_project_ids_for_resource_item('milestone', item.name)
                    if not ids_for_ms:
                        item.id_project = all_known_proj_ids  # Milestones without a project are for all
                        ms_project_ids = all_known_proj_ids  # This list is used to check if there is a ms for the proj
                    else:
                        item.id_project = ids_for_ms
            if data.get('versions'):
                for item in data.get('versions'):
                    ids_for_ver = self.smp_version.get_project_ids_for_resource_item('version', item.name)
                    if not ids_for_ver:
                        item.id_project = all_known_proj_ids  # Versions without a project are for all
                        vers_project_ids = all_known_proj_ids  # List is used to check if there is a version for proj
                    else:
                        item.id_project = ids_for_ver

            # TODO: don't access private filter data here. This may fail if filter plugin is disabled later on
            filtered_project_names = get_project_filter_settings(req, 'roadmap', 'smp_projects')

            if filtered_project_names and 'All' not in filtered_project_names:
                show_proj_ids = [project.id for project in usr_projects if project[1] in filtered_project_names]
            else:
                show_proj_ids = [pproject.id for pproject in usr_projects]

            data.update({'projects': usr_projects,
                         'show': req.args.get('show', []),  # TODO: is this used at all?
                         'projects_with_ms': ms_project_ids,  # Currently not used in the template
                         'projects_with_ver': vers_project_ids,  # Currently not used in the template
                         'visible_projects': show_proj_ids})

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'roadmap.html':
            # Change label to include versions
            filter_ = Transformer('//label[@for="showcompleted"]')
            stream |= filter_.replace(HTML(u'<label for="showcompleted">Show completed milestones</label>'))
            # Add additional checkboxes to preferences
            data['smp_render'] = 'prefs'  # specify which part of template to render

            group_proj = get_filter_settings(req, 'roadmap', 'smp_group')
            chked = ''
            if group_proj:
                chked = 'checked="1"'
            filter_ = Transformer('//form[@id="prefs"]')
            stream |= filter_.prepend(HTML(u'<div>'
                                            '<input type="hidden" name="smp_update" value="group" />'
                                            '<input type="checkbox" id="groupbyproject" name="smp_group" '
                                            'value="1" %s />'
                                            '<label for="groupbyproject">Group by project</label></div><br />' %
                                            chked))
            if chked:
                filter_ = Transformer('//div[@class="milestones"]')
                # Add new grouped content
                stream |= filter_.before(self.group_tmpl.generate(**data))
                # Remove old milestone contents
                stream |= filter_.remove()
        return stream


class SmpRoadmapModule(Component):
    """Manage roadmap page for projects"""

    implements(IRequestFilter)

    data_provider = OrderedExtensionsOption(
        'simple-multi-project', 'roadmap_data_provider', IRoadmapDataProvider,
        default="SmpRoadmapGroup, SmpRoadmapProjectFilter",
        doc="""Specify the order of plugins providing data for roadmap page""")

    data_filters = OrderedExtensionsOption(
        'simple-multi-project', 'roadmap_data_filters', IRoadmapDataProvider,
        default="SmpRoadmapGroup, SmpRoadmapProjectFilter",
        doc="""Specify the order of plugins filtering data for roadmap page""")

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
                for provider in self.data_provider:
                    data = provider.add_data(req, data)

                for provider in self.data_filters:
                    data = provider.filter_data(req, data)

        return template, data, content_type


class SmpRoadmapProjectFilter(Component):
    """Filter roadmap by project(s)"""

    implements(IRequestFilter, IRoadmapDataProvider)

    def __init__(self):
        self.smp_project = SmpProject(self.env)  # For create_projects_table
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_version = SmpVersion(self.env)

    # IRequestFilter

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        path_elms = req.path_info.split('/')
        if data and len(path_elms) > 1 and path_elms[1] == 'roadmap':
            # xpath: //form[@id="prefs"]
            filter_list = [{'pos': 'prepend',
                            'css': 'form#prefs',
                            'html': create_proj_table(self, req, 'roadmap')}]
            if filter_list:
                add_script_data(req, {'smp_filter': filter_list})
                add_script(req, 'simplemultiproject/js/smp_add_prefs.js')

        return template, data, content_type

    # IRoadmapDataProvider

    def add_data(self, req, data):
        return data

    def filter_data(self, req, data):

        filter_proj = get_project_filter_settings(req, 'roadmap', 'smp_projects', 'All')

        if 'All' in filter_proj:
            return data

        # Filter the given data
        # TODO: this data isn't necessarily available here because it is added in post_process_req() of SmpRoadmapGroup
        # which may be called after this. filter_data() is called by SmpRoadmapModule
        if 'projects' in data:
            filtered = []
            for project in data['projects']:
                if project[1] in filter_proj:
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
        sel = u' selected' if item[1] in filter_prj else u''
        options += option_tmpl.format(p_name=item[1], sel=sel)

    return div_templ.format(size=size, all_selected='' if filter_prj else u' selected', options=options)


def create_proj_table(self, req, session_name='roadmap'):
    """Create a select tag holding valid projects (means not closed) for
    the current user.

    @param self: Component instance holding a self.smp_project =  SmpProject(env)
    @param req      : Trac request object

    @return DIV tag holding a project select control with label
    """
    projects = self.smp_project.get_all_projects()
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
