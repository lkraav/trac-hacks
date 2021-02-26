# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Robert Barsch <barsch@egu.eu>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os
from ConfigParser import ConfigParser
from StringIO import StringIO

from trac.admin.api import IAdminPanelProvider
from trac.core import Component, TracError, implements
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider


class SVNAuthzPlugin(Component):

    implements(ITemplateProvider, IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm('admin', 'versioncontrol/authz'):
            yield ('versioncontrol', _("Version Control"),
                   'authz', _("Subversion Authz"))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm('admin', 'versioncontrol/authz').require('TRAC_ADMIN')

        # get default authz file from trac.ini
        authz_file = self.config.getpath('svn', 'authz_file')

        # test if authz file exists and is writable
        if not os.access(authz_file, os.W_OK | os.R_OK):
            raise TracError(_("Can't access authz file %(file)s",
                              file=authz_file))

        # evaluate forms
        if req.method == 'POST':
            current = req.args.get('current').strip().replace('\r', '')

            # encode to utf-8
            current = current.encode('utf-8')

            # parse and validate authz file with a config parser
            cp = ConfigParser()
            try:
                cp.readfp(StringIO(current))
            except Exception as e:
                raise TracError(_("Invalid Syntax: %(error)s", error=e))

            # write to disk
            try:
                with open(authz_file, 'wb') as fh:
                    fh.write(current)
            except Exception as e:
                raise TracError(_("Can't write authz file: %(error)s",
                                  error=e))

        # read current authz file
        current = ""
        try:
            with open(authz_file) as fh:
                current = fh.read()
        except:
            pass

        return 'svnauthz.html', {'auth_data': current}

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return []
