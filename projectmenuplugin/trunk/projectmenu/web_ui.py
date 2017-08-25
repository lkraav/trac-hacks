# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import posixpath

from genshi.builder import tag
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
    add_script
from trac.web.api import IRequestFilter
from trac.web.main import open_environment


class ProjectMenuModule(Component):

    implements(INavigationContributor, ITemplateProvider, IRequestFilter)

    # INavigationProvider methods

    def get_navigation_items(self, req):
        projects = []
        search_path, this_project = os.path.split(self.env.path)
        base_url, _ = posixpath.split(req.abs_href())

        for project in os.listdir(search_path):
            if project != this_project:
                proj_path = os.path.join(search_path, project)
                try:
                    proj_env = open_environment(proj_path, use_cache=True)
                except TracError:
                    continue

                proj_elm = tag.option(proj_env.project_name,
                                      value=posixpath.join(base_url, project))
                projects.append((proj_elm, proj_env.project_name))
        projects.append((tag.option(self.env.project_name,
                                    selected=True, value=''),
                         self.env.project_name,))
        # Sort on the project names
        projects.sort(lambda a, b: cmp(a[1], b[1]))

        yield ('metanav', 'projectmenu',
               tag.select([e for e, _ in projects], name='projectmenu',
                          id='projectmenu',
                          onchange='return on_projectmenu_change();'))

    def get_active_navigation_item(self, req):
        return ''

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('projectmenu', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        add_script(req, 'projectmenu/projectmenu.js')
        return handler

    def post_process_request(self, req, template, content_type):
        return template, content_type
