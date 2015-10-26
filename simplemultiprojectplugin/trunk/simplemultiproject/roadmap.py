# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from genshi.builder import tag
from genshi.filters.transform import Transformer
from genshi.input import HTML
from trac.util.text import to_unicode
from trac.core import *
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_stylesheet
from operator import itemgetter
from trac.wiki.formatter import wiki_to_html
from simplemultiproject.model import *
from simplemultiproject.model import smp_filter_settings, smp_settings
from trac import __version__ as VERSION
from simplemultiproject.smp_model import SmpProject, SmpMilestone

__all__ = ['SmpRoadmapGroup', 'SmpRoadmapProjectFilter']

class SmpRoadmapProjectFilter(Component):
    """Allows for filtering by 'Project'
    """

    implements(IRequestFilter, ITemplateStreamFilter)

    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/roadmap'):
            filter_projects = smp_filter_settings(req, 'roadmap', 'projects')

            if data:
                if filter_projects and len(filter_projects) > 0:
                    milestones = data.get('milestones')
                    milestones_stats = data.get('milestone_stats')

                    filtered_milestones = []
                    filtered_milestone_stats = []

                    if milestones:
                        for idx, milestone in enumerate(milestones):
                            milestone_name = milestone.name
                            project = self.__SmpModel.get_project_milestone(milestone_name)

                            if project and project[0] in filter_projects:
                                filtered_milestones.append(milestone)
                                filtered_milestone_stats.append(milestones_stats[idx])

                        data['milestones'] = filtered_milestones
                        data['milestone_stats'] = filtered_milestone_stats

                if VERSION <= '0.12':
                    data['infodivclass'] = 'info'
                else:
                    data['infodivclass'] = 'info trac-progress'

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename.startswith("roadmap"):
            filter_projects = smp_filter_settings(req, 'roadmap', 'projects')
            filter = Transformer('//form[@id="prefs"]/div[1]')
            stream = stream | filter.before(tag.label("Filter Projects:")) | filter.before(tag.br()) | \
                     filter.before(self._projects_field_input(req, filter_projects)) | filter.before(tag.br())

        return stream

    # Internal

    def _projects_field_input(self, req, selectedcomps):
        cursor = self.__SmpModel.get_all_projects_filtered_by_conditions(req)

        sorted_project_names_list = sorted(cursor, key=itemgetter(1))
        number_displayed_entries = len(sorted_project_names_list)+1     # +1 for special entry 'All'
        if number_displayed_entries > 15:
            number_displayed_entries = 15

        select = tag.select(name="filter-projects", id="Filter-Projects", multiple="multiple", size=("%s" % number_displayed_entries), style="overflow:auto;")
        select.append(tag.option("All", value="All"))

        for component in sorted_project_names_list:
            project = component[1]
            if selectedcomps and project in selectedcomps:
                select.append(tag.option(project, value=project, selected="selected"))
            else:
                select.append(tag.option(project, value=project))

        return select


######################################################################################################################
#     Everything below this point is (c) Cinc
######################################################################################################################

# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#
from trac.web.chrome import Chrome
from smp_model import SmpVersion

class SmpRoadmapGroup(Component):
    """Milestone and version grouping by project"""

    implements(IRequestFilter, ITemplateStreamFilter)

    def __init__(self):
        self.group_tmpl = Chrome(self.env).load_template("smp_roadmap.html")
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_project = SmpProject(self.env)
        self.smp_version = SmpVersion(self.env)
        self._SmpModel=SmpModel(self.env)

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        path_elms = req.path_info.split('/')
        if path_elms[1] == 'roadmap':
            # ITemplateProvider is implemented in another component
            add_stylesheet(req, "simplemultiproject/css/simplemultiproject.css")

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
                        vers_project_ids = all_known_proj_ids  # List is used to check if there is a version for the proj
                    else:
                        item.id_project = ids_for_ver

            filter_project = smp_filter_settings(req, 'roadmap', 'projects')
            if filter_project:
                l = []
                for p in usr_proj:
                    if p[1] in filter_project:
                        l.append(p[0])
                show_proj = l
            else:
                show_proj = [p[0] for p in usr_proj]

            data.update({'projects': usr_proj,
                        'hide': req.args.get('hide', []),
                        'show': req.args.get('show', []),
                        'projects_with_ms': ms_project_ids,  # Currently not used in the template
                        'projects_with_ver': vers_project_ids,  # Currently not used in the template
                        'visible_projects': show_proj})

        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):

        if filename == 'roadmap.html':
            # Change label to include versions
            filter_ = Transformer('//label[@for="showcompleted"]')
            stream = stream | filter_.replace(HTML('<label for="showcompleted">Show completed milestones and '
                                                   'versions</label>'))
            # Add additional checkboxes to preferences
            data['smp_render'] = 'prefs'
            chked = ''
            if 'group' in req.args:
                chked = 'checked="1"'
            filter_ = Transformer('//form[@id="prefs"]')
            stream = stream | filter_.prepend(HTML('<div>'
                                                   '<input type="checkbox" id="groupbyproject" name="group" '
                                                   'value="groupproject" %s />'
                                                   '<label for="groupbyproject">Group by project</label></div><br />' %
                                                    chked))
            if chked:
                # Remove contents leaving the preferences
                filter_ = Transformer('//div[@class="milestones"]')
                stream = stream | filter_.remove()
                # Add new grouped content
                filter_ = Transformer('//form[@id="prefs"]')
                stream = stream | filter_.after(self.group_tmpl.generate(**data))

        return stream
