# -*- coding: utf8 -*-
#
# Copyright (C) Cauly Kan, mail: cauliflower.kan@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

'''
Created on 2014-03-19 

@author: cauly
'''

from trac.core import Component, implements, TracError
from trac.ticket import Ticket
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from genshi.filters.transform import Transformer, StreamBuffer
from genshi.builder import tag

class FieldOfTablePlugin(Component):
    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider)

    def post_process_request(self, req, template, data, content_type):

        if ((req.path_info.startswith('/ticket') and \
            (req.perm.has_permission('TICKET_VIEW') or \
            req.perm.has_permission('TICKET_MODIFY')))
            or (req.path_info.startswith('/newticket')) and \
            req.perm.has_permission('TICKET_CREATE')):

            add_script(req, 'FieldOfTable/fot.js')
            add_stylesheet(req, 'FieldOfTable/fot.css')

        return template, data, content_type

    def filter_stream(self, req, method, filename, stream, data):

        if ((req.path_info.startswith('/ticket') and \
            (req.perm.has_permission('TICKET_VIEW') or \
            req.perm.has_permission('TICKET_MODIFY')))
            or (req.path_info.startswith('/newticket')) and \
            req.perm.has_permission('TICKET_CREATE')):

            for opt_name, opt_value in self.config.options('ticket-custom'):

                if '.' in opt_name and len(opt_name.split('.')) == 2 and opt_name.split('.')[1] == 'table':

                    field_name = opt_name.split('.')[0]

                    if self.config.has_option('ticket-custom', field_name) and \
                    self.config.get('ticket-custom', field_name) == 'textarea' and \
                    self.config.get('ticket-custom', field_name + '.format') == 'wiki':

                        stream |= Transformer('//textarea[@id="field-%s"]' % field_name).attr('columns', opt_value)

        return stream

    def pre_process_request(self, req, handler):
        return handler

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('FieldOfTable', resource_filename(__name__, 'htdoc'))]

    def get_templates_dirs(self):

        return []