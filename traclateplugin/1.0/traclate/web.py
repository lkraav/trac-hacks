# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Dirk Stöcker <trac@stoecker.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs.

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider
from trac.util.translation import domain_functions

_, add_domain, ngettext = domain_functions(
    'traclate',
    ('_', 'add_domain', 'ngettext'))

__all__ = ['TraclateRequestHandler']

class TraclateRequestHandler(Component):
    """Interface to allow users to translate texts."""

    def __init__(self):
        """Set up translation domain"""
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    implements(IRequestHandler, ITemplateProvider, IPermissionRequestor)

    # IRequestHandler

    def match_request(self, req):
        return req.path_info == '/translate'

    def process_request(self, req):
        raise Exception("Not implemented")

    # ITemplateProvider

    def get_htdocs_dirs(self):
        return [('traclate', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # IPermissionRequestor

    def get_permission_actions(self):
        return ['TRANS_CONFIG', 'TRANS_ADD', 'TRANS_MODIFY', 'TRANS_MODIFYREVIEWED',
                'TRANS_REVIEW', 'TRANS_VIEW',
                ('TRANS_EDIT', ['TRANS_VIEW', 'TRANS_ADD', 'TRANS_MODIFY', 'TRANS_MODIFYREVIEWED']),
                ('TRANS_ADMIN', ['TRANS_CONFIG', 'TRANS_EDIT', 'TRANS_REVIEW'])]
