# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2009-2011 Radu Gasler <miezuit@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import urllib

from trac.admin.api import AdminCommandError, IAdminCommandProvider, \
    IAdminPanelProvider
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.wiki.api import WikiSystem
from trac.web.chrome import ITemplateProvider, add_notice, add_warning

from wikireplace.util import wiki_text_replace


class WikiReplaceModule(Component):
    """An evil module that adds a replace button to the wiki UI."""

    implements(IAdminCommandProvider, IAdminPanelProvider,
               IPermissionRequestor, IRequestFilter, ITemplateProvider)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['WIKI_REPLACE', ('WIKI_ADMIN', ['WIKI_REPLACE'])]

    # IAdminCommandProvider

    def get_admin_commands(self):
        yield ('wiki sub', '<old-text> <new-text> <pages>',
               "Substitute wiki text",
               self._complete_sub, self._do_sub)

    def _complete_sub(self, args):
        if len(args) >= 3:
            return WikiSystem(self.env).pages

    def _do_sub(self, oldtext, newtext, *wikipages):
        wiki_text_replace(self.env, oldtext, newtext, wikipages, 'trac')

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'WIKI_REPLACE' in req.perm('wiki'):
            yield 'general', 'General', 'wikireplace', 'Wiki Replace'

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('WIKI_REPLACE')
        wikipages = urllib.unquote_plus(req.args.get('wikipages', ''))
        parts = wikipages.splitlines()

        data = {
            'find': urllib.unquote_plus(req.args.get('find', '')),
            'replace': urllib.unquote_plus(req.args.get('replace', '')),
            'wikipages': parts,
            'redir': req.args.get('redirect', '') == '1',
        }

        if req.method == 'POST':
            # Check that required fields are filled in.
            if not data['find']:
                add_warning(req, 'The Find field was empty. '
                                 'Nothing was changed.')
            if not data['wikipages'] or not data['wikipages'][0]:
                add_warning(req, 'The Wiki pages field was empty. '
                                 'Nothing was changed.')

            # Replace text if the find and wikipages fields have been input.
            if data['find'] and data['wikipages'] and data['wikipages'][0]:
                add_notice(req, 'Replaced "%s" with "%s". See the timeline '
                                'for modified pages.' % (data['find'],
                                                         data['replace']))
                wiki_text_replace(self.env, data['find'], data['replace'],
                                  data['wikipages'], req.authname)

            # Reset for the next display
            data['find'] = ''
            data['replace'] = ''
            data['wikipages'] = ''

        return 'admin_wikireplace.html', data

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if (req.path_info.startswith('/wiki') or req.path_info == '/') \
                and data:
            page = data.get('page')
            if not page:
                return template, data, content_type
        return template, data, content_type
