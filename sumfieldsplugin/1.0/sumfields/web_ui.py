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
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data


class SumFieldsModule(Component):
    """A module that sums fields/columns using JS/jQuery."""

    fields = ListOption('sumfields', 'fields', default=[],
                        doc="Fields to sum in custom query reports.")

    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith(('/milestone', '/roadmap')) or \
                (req.path_info.startswith(('/query', '/report')) and
                 'REPORT_VIEW' in req.perm):
            add_script(req, 'sumfields/sumfields.js')
            add_script_data(req, fields=self.fields)
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('sumfields', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
