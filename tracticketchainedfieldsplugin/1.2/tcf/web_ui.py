# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The TracTicketChainedFields Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#----------------------------------------------------------------------------

import inspect
import json
import os
import textwrap
import time
from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.db import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.util.html import html
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_script)
from trac.web.api import (
    IRequestHandler, ITemplateStreamFilter, RequestDone)

from trac.admin import IAdminPanelProvider
from trac.ticket import (
    ITicketManipulator, Milestone, Ticket, TicketSystem)

from model import (
    schema, schema_version, TracTicketChainedFields_List)

__all__ = ['TracTicketChainedFieldsModule']


class TracTicketChainedFieldsModule(Component):

    implements(IAdminPanelProvider,
               IEnvironmentSetupParticipant,
               IPermissionRequestor,
               IRequestHandler,
               ITemplateProvider,
               ITemplateStreamFilter,
               )

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TCF_ADMIN', 'TCF_VIEW']

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        dbm = DatabaseManager(self.env)
        dbm.create_tables(schema)
        dbm.set_database_version(schema_version, 'tcf_version')

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(schema_version, 'tcf_version')

    def upgrade_environment(self):
        self.environment_created()

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('tcf', resource_filename(__name__, 'htdocs'))]

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            add_script(req, 'tcf/tcf_ticket.js')
        return stream

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TCF_ADMIN' in req.perm:
            yield 'ticket', 'Ticket System', 'tcf_admin', \
                  'Chained Fields'

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TCF_ADMIN')

        data = {}

        if req.method == 'POST':
            if 'save' in req.args:
                tcf_define_json = req.args.get('tcf_define', '').strip()

                try:
                    json.loads(tcf_define_json)
                except:
                    raise TracError("Format error, which should be JSON. Please back to last page and check the configuration.")

                TracTicketChainedFields_List.insert(self.env, tcf_define_json)

                req.redirect(req.abs_href.admin(cat, page))

        else:
            data['tcf_define'] = TracTicketChainedFields_List.get_tcf_define(self.env)
            return 'tcf_admin.html', data

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/tcf')

    def process_request(self, req):
        hide_empty_fields = \
            self.config.getbool('tcf', 'hide_empty_fields', False)
        chained_fields = self.config.getlist('tcf', 'chained_fields', [])

        if req.path_info.startswith('/tcf/query_tcf_define'):
            # handle XMLHTTPRequest
            result = {
                'status': '1',
                'hide_empty_fields': hide_empty_fields,
                'chained_fields': chained_fields,
            }

            tcf_define = TracTicketChainedFields_List.get_tcf_define(self.env)
            try:
                result['tcf_define'] = json.loads(tcf_define)
            except:
                pass

            if 'warning' in req.args:
                result['warning'] = '1'
            jsonstr = json.dumps(result)
            self._send_response(req, jsonstr)

        elif req.path_info.startswith('/tcf/query_field_change'):
            result = {
                'status': '1',
                'hide_empty_fields': hide_empty_fields,
            }

            trigger = req.args.get('trigger', '')
            if trigger.startswith('field-'):
                trigger = trigger[len('field-'):]
            trigger_value = req.args.get('field-' + trigger, '')
            if not trigger:
                result['status'] = '0'

            tcf_define = TracTicketChainedFields_List. \
                         get_tcf_define(self.env)
            try:
                tcf_define_target = json.loads(tcf_define)
            except:
                pass

            def locate_trigger_values(root):
                if trigger in root:
                    return root[trigger].get(trigger_value)
                for field, field_values in root.items():
                    field_value = req.args.get('field-' + field, '')
                    if not field_value:
                        # skip field not specified
                        continue
                    trigger_values = locate_trigger_values(field_values.get(field_value, {}))
                    if trigger_values:
                        # return when found
                        return trigger_values

            trigger_values = locate_trigger_values(tcf_define_target)

            target_options = []
            targets = []
            if trigger_values:
                for k, v in trigger_values.items():
                    target_field = k
                    target_options = [target_option for target_option in v.keys() if target_option]
                    target_options.sort(cmp=lambda x, y: cmp(x.lower(), y.lower()))

                    targets.append({
                        'target_field': target_field,
                        'target_options': target_options,
                    })

            result['targets'] = targets

            if 'warning' in req.args:
                result['warning'] = '1'
            jsonstr = json.dumps(result)
            self._send_response(req, jsonstr)

    # Internal methods

    def _send_response(self, req, message):
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain' + ';charset=utf-8')
        req.send_header('Content-Length',
                        len(isinstance(message, unicode) and
                            message.encode('utf-8') or message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone
