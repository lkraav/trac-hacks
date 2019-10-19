#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013, 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import implements, Component
from trac.ticket.default_workflow import get_workflow_config
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_script_data
from pkg_resources import resource_filename
import json


class TicketValidatorDecolator(Component):
    implements(ITemplateProvider, IRequestFilter, IRequestHandler)

    def __init__(self):
        self.rules = self._get_validation_rules()
        self.workflow = get_workflow_config(self.config)

    def _get_validation_rules(self):
        sentinel = 'sentinel'  # something that isn't None
        conditionkeys = ['status', 'type']
        conditionkeys.sort()
        rules = {'status=new&type=*': {'summary': sentinel}}
        ''' compatible with TracTicketConditionalValidateFieldsPlugin '''

        try:
            from tracticketconditionalvalidatefield.api import TicketsValidator
            if self.compmgr.is_enabled(TicketsValidator):
                types = [k for k, v in self.config.options('ticket_validate') if k.find('.') == -1]
                for ticket_type in types:
                    fields = self.config.getlist('ticket_validate', ticket_type)
                    condition = 'status=*&type=%s' % ticket_type
                    if condition not in rules:
                        rules[condition] = {}
                    rule = rules.get(condition)
                    for field in fields:
                        rule[field] = self.config.get('ticket_validate', '%s.tip' % field, default=sentinel)
        except:
            pass

        ''' compatible with TracTicketValidatorPlugin '''
        try:
            from tracticketvalidator.ticketvalidator import TicketValidator
            if self.compmgr.is_enabled(TicketValidator):
                keys = [k[:-4] for k, v in self.config.options('ticketvalidator') if k.endswith('.rule')]  # includes dot
                for key in keys:
                    values = dict([(k[len(key):], v) for k, v in self.config.options('ticketvalidator') if k.startswith(key)])
                    condition = '&'.join(['%s=%s' % (ck, values.get(ck, '*')) for ck in conditionkeys])
                    if condition not in rules:
                        rules[condition] = {}
                    rule = rules.get(condition)
                    field = values.get('field', key[:-1])
                    rule[field] = values.get('tip', sentinel)
        except:
            pass
        return rules

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/ticketvalidator.options'

    def process_request(self, req):
        ''' return validation rules in json '''
        content = json.dumps({'rules': self.rules, 'workflow': self.workflow}, indent=4)
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(content))
        req.end_headers()
        req.write(content)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler  # unchanged

    def post_process_request(self, req, template, data, content_type):
        if template in [
                        'ticket.html',  # /ticket/{\d} or /newticket
                        ]:
            add_script(req, "contextchrome/js/ticketvalidatordecolator.js")
            status = 'ticket' in data and 'status' in data['ticket'].values and data['ticket'].values['status'] or 'sentinel'
            add_script_data(req, {"contextchrome_tracstatus": status})
            add_script_data(req, contextchrome_ticketvalidator={'rules': self.rules, 'workflow': self.workflow})
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
