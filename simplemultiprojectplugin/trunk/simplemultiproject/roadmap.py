# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#

from genshi.template import MarkupTemplate
from genshi import HTML
from genshi.filters import Transformer
from trac.config import OrderedExtensionsOption
from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import Chrome, add_stylesheet

from simplemultiproject.smp_model import SmpMilestone, SmpProject, SmpVersion
from simplemultiproject.api import IRoadmapDataProvider
from simplemultiproject.model import SmpModel
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
        self._SmpModel = SmpModel(self.env)

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
            # Get list of projects for this user. Any permission filter is applied
            all_proj = self._SmpModel.get_all_projects_filtered_by_conditions(req)  # This is a list of tuples
            usr_proj = [project for project in sorted(all_proj, key=lambda k: k[1])]
            all_known_proj_ids = [p[0] for p in usr_proj]

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
            filter_project = get_project_filter_settings(req, 'roadmap', 'smp_projects')

            if filter_project and 'All' not in filter_project:
                l = []
                for p in usr_proj:
                    if p[1] in filter_project:
                        l.append(p[0])
                show_proj = l
            else:
                show_proj = [p[0] for p in usr_proj]

            data.update({'projects': usr_proj,
                         'show': req.args.get('show', []),  # TODO: is this used at all?
                         'projects_with_ms': ms_project_ids,  # Currently not used in the template
                         'projects_with_ver': vers_project_ids,  # Currently not used in the template
                         'visible_projects': show_proj})

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'roadmap.html':
            # Change label to include versions
            filter_ = Transformer('//label[@for="showcompleted"]')
            stream |= filter_.replace(HTML(u'<label for="showcompleted">Show completed milestones and '
                                                   'versions</label>'))
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
                # Remove contents leaving the preferences
                filter_ = Transformer('//div[@class="milestones"]')
                stream |= filter_.remove()
                # Add new grouped content
                filter_ = Transformer('//form[@id="prefs"]')
                stream |= filter_.after(self.group_tmpl.generate(**data))

        return stream


class SmpRoadmapModule(Component):
    """Manage roadmap page for projects"""

    implements(IRequestFilter)

    data_provider = OrderedExtensionsOption(
        'simple-multi-project', 'roadmap_data_provider', IRoadmapDataProvider,
        default="SmpVersionProject, SmpRoadmapGroup, SmpRoadmapProjectFilter",
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

    implements(ITemplateStreamFilter, IRoadmapDataProvider)

    def __init__(self):
        self._SmpModel = SmpModel(self.env)
        self.smp_project = SmpProject(self.env)  # For create_projects_table
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_version = SmpVersion(self.env)

    # IRoadmapDataProvider

    def add_data(self, req, data):
        return data

    def filter_data(self, req, data):

        filter_proj = \
            get_project_filter_settings(req, 'roadmap', 'smp_projects', 'All')

        if 'All' in filter_proj:
            return data

        # Filter the given data
        if 'projects' in data:
            filtered = []
            for p in data['projects']:
                if p[1] in filter_proj:
                    filtered.append(p)
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
        path_elms = req.path_info.split('/')
        if len(path_elms) > 1 and path_elms[1] == 'roadmap':
            # Add project selection to the roadmap preferences
            xformer = Transformer('//form[@id="prefs"]')
            stream |= xformer.prepend(create_proj_table(self, self._SmpModel, req))

        return stream


# Genshi template for creating the project selection
table_proj = """
<div xmlns:py="http://genshi.edgewall.org/"  style="overflow:hidden;">
<div>
<label>Filter Project:</label>
</div>
<div>
<input type="hidden" name="smp_update" value="filter" />
<select id="Filter-Projects" name="smp_projects" multiple="multiple" size="$size" style="overflow:auto;">
    <option value="All" >All</option>
    <option py:for="prj in all_projects" value="${prj[1]}" selected="${'selected' if prj[1] in filter_prj else None}">
        ${prj[1]}
    </option>
</select>
</div>
<br />
</div>
"""


def create_proj_table(self, _SmpModel, req):
    """Create a select tag holding valid projects (means not closed) for
    the current user.

    @param self: Component instance holding a self.smp_project =  SmpProject(env)
    @param _SmpModel: SmpModel object used for filtering functions
    @param req      : Trac request object

    @return DIV tag holding a project select control with label
    """
    # project[0] is the id, project[1] the name
    all_projects = [[project[0], project[1]] for project in self.smp_project.get_all_projects()]
    all_project_names = [name for p_id, name in all_projects]

    # no closed projects
    for project_name in all_project_names:
        project_info = _SmpModel.get_project_info(project_name)
        _SmpModel.filter_project_by_conditions(all_project_names, project_name, project_info, req)

    filtered_projects = [[p_id, project_name] for p_id, project_name in all_projects
                         if project_name in all_project_names]
    if filtered_projects:
        size = len(filtered_projects) + 1  # Account for 'All' option
    else:
        return MarkupTemplate('<div xmlns:py="http://genshi.edgewall.org/">'
                              '<p>No projects defined.</p>'
                              '<br />'
                              '</div>').generate()
    if size > 5:
        size = 5

    filter_prj = get_project_filter_settings(req, 'roadmap', 'smp_projects', 'All')  # list of currently selected projects
    if 'All' in filter_prj:
        filter_prj = []
    tbl = MarkupTemplate(table_proj)
    return tbl.generate(all_projects=filtered_projects, filter_prj=filter_prj, size=size)
