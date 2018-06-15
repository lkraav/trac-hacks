# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Ryan Ollos
# Copyright (C) 2012-2013 Olemis Lang
# Copyright (C) 2008-2009 Noah Kantrowitz
# Copyright (C) 2008 Christoper Lenz
# Copyright (C) 2007-2008 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.prefs.api import IPreferencePanelProvider
from trac.util.html import html as tag
from trac.web import IRequestHandler
from trac.web.chrome import Chrome, INavigationContributor, ITemplateProvider

__all__ = ['DeveloperPlugin']


class DeveloperPlugin(Component):
    implements(INavigationContributor, IPermissionRequestor,
               IPreferencePanelProvider, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'developer'

    def get_navigation_items(self, req):
        if 'TRAC_DEVELOP' in req.perm:
            yield ('metanav', 'developer',
                   tag.a('Developer Tools', href=req.href.developer()))

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TRAC_DEVELOP']

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/developer/?$', req.path_info)

    def process_request(self, req):
        req.perm.require('TRAC_DEVELOP')
        return 'developer/index.html', {}, None

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracdeveloper', 'templates'),
                resource_filename('tracdeveloper.dozer', 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('developer', resource_filename('tracdeveloper', 'htdocs')),
                ('dozer', resource_filename('tracdeveloper.dozer', 'htdocs'))]

    # IPreferencePanelProvider methods

    def get_preference_panels(self, req):
        if 'TRAC_DEVELOP' in req.perm:
            yield 'developer', 'Developer Options'

    def render_preference_panel(self, req, panel):
        # JIC
        req.perm.require('TRAC_DEVELOP')
        if req.method == 'POST':
            key = 'developer.js.enable_debug'
            req.session[key] = req.args.get('enable_debug', '0')
        if hasattr(Chrome(self.env), 'jenv'):
            return 'developer/prefs_developer.html', {}, None
        else:
            return 'developer/prefs_developer.html', {}
