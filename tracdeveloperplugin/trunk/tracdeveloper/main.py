# -*- coding: utf-8 -*-

import re

from genshi.builder import tag
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.prefs.api import IPreferencePanelProvider

__all__ = ['DeveloperPlugin']


class DeveloperPlugin(Component):
    implements(INavigationContributor, IPermissionRequestor,
               IPreferencePanelProvider, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'developer'

    def get_navigation_items(self, req):
        if req.perm.has_permission('TRAC_DEVELOP'):
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
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('developer', resource_filename(__name__, 'htdocs'))]

    # IPreferencePanelProvider methods
    def get_preference_panels(self, req):
        if req.perm.has_permission('TRAC_DEVELOP'):
            yield 'developer', 'Developer Options'

    def render_preference_panel(self, req, panel):
        # JIC
        req.perm.require('TRAC_DEVELOP')
        if req.method == 'POST':
            key = 'developer.js.enable_debug'
            req.session[key] = req.args.get('enable_debug', '0')
        return 'developer/prefs_developer.html', {}

