# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2010 Alvaro J. Iradier <alvaro.iradier@polartech.es>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import posixpath

from trac.config import ListOption
from trac.core import Component, TracError, implements
from trac.env import open_environment
from trac.perm import IPermissionRequestor
from trac.search.api import ISearchSource
from trac.search.web_ui import SearchModule
from trac.util.datefmt import to_datetime
from trac.util.html import Markup
from trac.util.text import to_unicode
from trac.web.href import Href


class SearchAllPlugin(Component):
    """Search the source repository."""

    implements(IPermissionRequestor, ISearchSource)

    include_projects = ListOption('searchall', 'include_projects', [],
        doc="""Comma separated list of projects to include in
        'Search All Projects'. If empty, all projects will be searched.
        Case sensitive.
        """)

    exclude_projects = ListOption('searchall', 'exclude_projects', [],
        doc="""Comma separated list of projects to exclude in
        'Search All Projects'. Case sensitive.
        """)

    # ISearchSource methods

    def get_search_filters(self, req):

        if 'SEARCHALL_VIEW' not in req.perm:
            return

        if hasattr(req, 'is_searchall_recursive'):
            return

        req.is_searchall_recursive = True

        # Check what filters are available in current project
        existing_filters = []
        env_search = SearchModule(self.env)
        for source in env_search.search_sources:
            if source == self:
                continue
            existing_filters += source.get_search_filters(req)

        # Now get the filters available in other projects
        projects = self.get_project_list(req)
        for project, project_path, project_url, env in projects:
            env_search = SearchModule(env)

            available_filters = []
            for source in env_search.search_sources:
                available_filters += source.get_search_filters(req)

            for filter in available_filters:
                if filter in existing_filters:
                    continue
                existing_filters.append(filter)
                yield filter

        yield 'searchall', 'All projects', 0

    def get_search_results(self, req, query, filters):
        # return if search all is not active
        if 'searchall' not in filters:
            return

        if 'SEARCHALL_VIEW' not in req.perm:
            return

        # remove 'searchall' from filters
        subfilters = []
        for filter in filters:
            if not filter == 'searchall':
                subfilters.append(filter)
        # don't do anything if we have no filters
        if not subfilters:
            return

        projects = self.get_project_list(req)

        for project, project_path, project_url, env in projects:

            results = []
            env_search = SearchModule(env)

            #available_filters = []
            # for source in env_search.search_sources:
            #    available_filters += source.get_search_filters(req)
            #subfilters = [x[0] for x in available_filters if x[0] != 'searchall']

            self.log.debug("Searching project %s", project)
            self.log.debug("Searching for %s", query[0])
            self.log.debug("Searching with filters %s", subfilters)

            # Update request data
            orig_href = req.href
            req.href = Href(project_url)

            for source in env_search.search_sources:
                for filter in subfilters:
                    try:
                        results += list(source.get_search_results(req, query,
                                                                  [filter]))
                    except Exception, ex:
                        results += [
                            (req.href('search', **req.args),
                             "<strong>ERROR</strong> in search filter "
                             "<em>%s</em>" % filter,
                             to_datetime(None), "none",
                             "Exception: %s" % to_unicode(ex))]

            req.href = orig_href

            for result in results:
                yield (result[0],
                       Markup('<span class="searchall_project">%s</span><br/> %s'
                              % (env.project_name, result[1]))) \
                    + result[2:]

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['SEARCHALL_VIEW', ('TRAC_ADMIN', ['SEARCHALL_VIEW'])]

    # Internal methods

    def get_project_list(self, req):
        # get search path and base_url
        search_path, this_project = os.path.split(self.env.path)
        base_url = posixpath.split(req.abs_href())[0]

        projects = []
        for project in os.listdir(search_path):

            # skip our own project
            if project == this_project:
                continue

            # Include only if project is in include_projects, or
            # include_projects is empty
            if self.include_projects and project not in self.include_projects:
                continue

            # Exclude if project is in exclude_projcets
            if project in self.exclude_projects:
                continue

            # make up URL for project
            project_url = '/'.join((base_url, project))
            project_path = os.path.join(search_path, project)

            if not os.path.isdir(project_path):
                continue
            try:
                env = open_environment(project_path, use_cache=True)
            except TracError:
                continue

            projects.append((project, project_path, project_url, env))

        return projects
