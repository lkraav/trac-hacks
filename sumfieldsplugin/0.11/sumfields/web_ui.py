# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2013 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.config import ListOption
from trac.core import *
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script


class SumFieldsModule(Component):
    """A module that sums fields/columns using JS/jQuery."""

    fields = ListOption('sumfields', 'fields', default=[],
            doc="fields to sum in custom query reports.")

    implements(IRequestFilter, IRequestHandler, ITemplateProvider)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if (req.path_info.startswith('/query') or \
            req.path_info.startswith('/report')) \
          and req.perm.has_permission('REPORT_VIEW'):
            add_script(req, '/sumfields/sumfields.html')
        return template, data, content_type

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/sumfields')

    def process_request(self, req):
        data = {'fields':self.fields}
        return 'sumfields.html', {'data': data},'text/javascript'

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
