# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from __future__ import with_statement

import inspect
import textwrap
import time
import urllib
from pkg_resources import resource_filename

from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.admin.api import IAdminCommandProvider, IAdminPanelProvider
from trac.core import *
from trac.config import BoolOption, ListOption, Option
from trac.db import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.ticket import Ticket, Type as TicketType
from trac.web.api import IRequestHandler, ITemplateStreamFilter, RequestDone
from trac.web.chrome import Chrome, ITemplateProvider, add_script

try:
    import json
except ImportError:
    import simplejson as json

from tickettemplate.model import TT_Template, schema, schema_version
from utils import *

from i18n_domain import gettext, _, tag_, N_, add_domain

from default_templates import DEFAULT_TEMPLATES

__all__ = ['TicketTemplateModule']


class TicketTemplateModule(Component):

    implements(IAdminCommandProvider, IAdminPanelProvider,
               IEnvironmentSetupParticipant, IPermissionRequestor,
               IRequestHandler, ITemplateProvider, ITemplateStreamFilter)

    SECTION_NAME = 'tickettemplate'

    enable_custom = BoolOption(SECTION_NAME, 'enable_custom', True,
        """Display the My Template sidebar.""")

    field_list = ListOption(SECTION_NAME, 'field_list',
        'summary, description, reporter, owner, priority, cc, milestone, '
        'component, version, type',
        doc="""List of fields that can be included in the template.""")

    json_template_file = Option(SECTION_NAME, 'json_template_file', '',
        """File containing templates.""")

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['TT_USER', ('TT_ADMIN', ['TT_USER'])]
        return actions

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        # Create the required tables
        connector, _ = DatabaseManager(self.env)._get_connector()
        with self.env.db_transaction as db:
            for table in schema:
                for stmt in connector.to_sql(table):
                    db(stmt)
            db("""INSERT INTO system (name,value)
                  VALUES ('tt_version', %s)
               """, (schema_version,))

        # Create some default templates

        if self.json_template_file == '':
            # use default templates from module
            self._insert_templates(DEFAULT_TEMPLATES)
        else:
            self.ticket_template_import(self.json_template_file)

    def environment_needs_upgrade(self, db=None):
        for value, in self.env.db_query("""
                SELECT value FROM system WHERE name='tt_version'
                """):
            return int(value) < schema_version
        return True

    def upgrade_environment(self, db=None):
        for value, in self.env.db_query("""
                SELECT value FROM system WHERE name='tt_version'
                """):
            current_version = int(value)
            break
        else:
            self.environment_created()
            current_version = 0

        from tickettemplate import upgrades
        for version in range(current_version + 1, schema_version + 1):
            for function in upgrades.map.get(version):
                print textwrap.fill(inspect.getdoc(function))
                function(self.env, db)
                print 'Done.'
        self.env.db_transaction("""
            UPDATE system SET value=%s WHERE name='tt_version'
            """, (schema_version,))
        self.log.info("Upgraded tt tables from version %d to %d",
                      current_version, schema_version)

    def _insert_templates(self, templates):
        """
        accept list of tuples called templates and insert into database.
        example: templates = [('tt_name','tt_value'),]
        """
        now = int(time.time())
        for tt_name, tt_value in templates:
            record = [
                now,
                SYSTEM_USER,
                tt_name,
                'description',
                tt_value,
            ]
            TT_Template.insert(self.env, record)
            # increment timestamp; other code expects it to be unique
            now += 1

    # IAdminCommandProvider methods

    def get_admin_commands(self):
        """Implement get_admin_commands to provide two trac-admin commands:

        *ticket_template export*
            export ticket_templates as json to stdout

        *ticket_template import <json_template_file>*
            import ticket_templates from json file specified in trac.ini
        """
        yield ('ticket_template export', '',
               """export ticket templates as json to stdout""",
               None, self.ticket_template_export)

        yield ('ticket_template import', '<json_template_file>',
               """import ticket templates from json file

               Specify json file path via:
               * json_template_file argument
               * json_template_file option in trac.ini
               """,
               None, self.ticket_template_import)

    def ticket_template_export(self):
        """export current ticket templates as json to stdout"""
        template_names = TT_Template.fetchNames(self.env)
        export_data = []
        for template_name in template_names:
            export_datum = (
                template_name,
                TT_Template.fetch(self.env, template_name),
            )
            export_data.append(export_datum)
        print(json.dumps(export_data, indent=2))

    def ticket_template_import(self, json_template_file=''):
        """
        Import ticket templates from json file.
        Specify json file path via:
         * json_template_file argument
         * json_template_file option in trac.ini
        """
        json_template_file = json_template_file or self.json_template_file
        if json_template_file or self.json_template_file:
            # convert template_file json to python data structure then insert
            with open(json_template_file) as f:
                self._insert_templates(json.load(f))

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TT_ADMIN' in req.perm:
            yield ('ticket', _("Ticket System"), self.SECTION_NAME,
                   _("Ticket Template"))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TT_ADMIN')

        data = {
            'gettext': gettext,
            '_': _,
            'tag_': tag_,
            'N_': N_,
        }

        data['options'] = [t.name for t in TicketType.select(self.env)] + \
                          [_("default")]
        data['type'] = req.args.get('type')

        if 'id' in req.args:
            # after load history
            id = req.args.get('id')
            data['tt_text'] = self._loadTemplateTextById(id)
            data['type'] = self._getNameById(id)

        elif req.method == 'POST':

            # Load
            if req.args.get('loadtickettemplate'):
                tt_name = req.args.get('type')

                data['tt_text'] = self._loadTemplateText(tt_name)

            # Load history
            if req.args.get('loadhistory'):
                tt_name = req.args.get('type')

                data['tt_name'] = tt_name

                tt_history = []
                for id, modi_time, tt_name, tt_text \
                        in TT_Template.selectByName(self.env, tt_name):
                    history = {'id': id, 'tt_name': tt_name,
                               'modi_time': self._formatTime(int(modi_time)),
                               'tt_text': tt_text,
                               'href': req.abs_href.admin(cat, page,
                                                          {'id': id})}
                    tt_history.append(history)

                data['tt_history'] = tt_history

                return 'loadhistory.html', data

            # Save
            elif req.args.get('savetickettemplate'):
                tt_text = req.args.get('description').replace('\r', '')
                tt_name = req.args.get('type')

                self._saveTemplateText(tt_name, tt_text)
                data['tt_text'] = tt_text

            # preview
            elif req.args.get('preview'):
                tt_text = req.args.get('description').replace('\r', '')
                tt_name = req.args.get('type')

                description_preview = \
                    self._previewTemplateText(tt_name, tt_text, req)
                data['tt_text'] = tt_text
                data['description_preview'] = description_preview

        return 'admin_tickettemplate.html', data

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('tt', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/tt')

    def process_request(self, req):
        req.perm.assert_permission('TICKET_CREATE')
        data = {
            'gettext': gettext,
            '_': _,
            'tag_': tag_,
            'N_': N_,
        }

        if req.path_info.startswith('/tt/query'):
            # handle XMLHTTPRequest
            data['req_args'] = req.args

            data.update({'tt_user': req.authname})
            result = TT_Template.fetchAll(self.env, data)
            result['status'] = '1'
            result['field_list'] = self._getFieldList()
            if self.enable_custom and 'TT_USER' in req.perm:
                result['enable_custom'] = True
            else:
                result['enable_custom'] = False
            if 'warning' in req.args:
                result['warning'] = req.args['warning']
            json_str = json.dumps(result)
            self._sendResponse(req, json_str)

        # tt_custom save
        elif req.path_info.startswith('/tt/custom_save'):
            tt_name, custom_template = self._handleCustomSave(req)
            result = {'status': '1', 'tt_name': tt_name,
                      'new_template': custom_template}
            json_str = json.dumps(result)
            self._sendResponse(req, json_str)

        # tt_custom delete
        elif req.path_info.startswith('/tt/custom_delete'):
            tt_name = self._handleCustomDelete(req)
            result = {'status': '1', 'tt_name': tt_name}
            json_str = json.dumps(result)
            self._sendResponse(req, json_str)

        elif req.path_info.startswith('/tt/edit_buffer_save'):
            tt_name, custom_template = self._handleCustomSave(req)
            result = {'status': '1', 'tt_name': tt_name,
                      'new_template': custom_template}
            json_str = json.dumps(result)
            self._sendResponse(req, json_str)
        elif req.path_info.startswith('/tt/tt_newticket.js'):
            filename = resource_filename(__name__,
                                         'templates/tt_newticket.js')
            chrome = Chrome(self.env)
            message = \
                chrome.render_template(req, filename, data, 'text/plain')

            req.send_response(200)
            req.send_header('Cache-control', 'no-cache')
            req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
            req.send_header('Content-Type', 'text/x-javascript')
            req.send_header('Content-Length',
                            len(isinstance(message, unicode)
                            and message.encode("utf-8") or message))
            req.end_headers()

            if req.method != 'HEAD':
                req.write(message)
            raise RequestDone

    # ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' \
                and req.path_info.startswith('/newticket'):
            # common js files
            add_script(req, 'tt/json2.js')

            stream = stream | Transformer('body').append(
                tag.script("preview = %s;" % ('true' if 'preview' in req.args else 'false')) +
                tag.script(type='text/javascript',
                src=req.href('tt', 'tt_newticket.js'))()
            )

        return stream

    # Internal methods

    def _handleCustomDelete(self, req):
        """ delete custom template
        """
        jsonstr = urllib.unquote(req.read())
        custom_data = json.loads(jsonstr)
        tt_name = custom_data.get('tt_name')
        if not tt_name:
            return

        tt_user = req.authname

        # delete same custom template if exist
        delete_data = {
            'tt_user': tt_user,
            'tt_name': tt_name,
        }
        TT_Template.deleteCustom(self.env, delete_data)
        return tt_name

    def _handleCustomSave(self, req):
        """ save custom template
        """
        jsonstr = urllib.unquote(req.read())
        custom_data = json.loads(jsonstr)
        tt_name = custom_data.get('tt_name')
        custom_template = custom_data.get('custom_template')
        if not tt_name or not custom_template:
            return tt_name, custom_template

        now = int(time.time())
        tt_user = req.authname

        # delete same custom template if exist
        delete_data = {
            'tt_user': tt_user,
            'tt_name': tt_name,
        }
        TT_Template.deleteCustom(self.env, delete_data)

        # save custom template
        field_list = self._getFieldList()
        for tt_field in field_list:
            tt_value = custom_template.get(tt_field)

            if tt_value is not None:
                record = [
                    now,
                    tt_user,
                    tt_name,
                    tt_field,
                    tt_value,
                ]
                TT_Template.insert(self.env, record)

        return tt_name, custom_template

    def _getFieldList(self):
        """ Get available fields
            return:
                ["summary", "description", ...]
        """
        field_list = [field.lower() for field in self.field_list]
        if 'description' not in field_list:
            field_list.append('description')
        return field_list

    def _getTTFields(self, tt_user, tt_name):
        """
            Get all fields values
            return:
                {
                    "summary": {"field_type":"text", "field_value": "abc"},
                    "description": {"field_type":"textarea", "field_value": "xyz"},
                }

        """
        result = {}

        # init result
        field_list = self._getFieldList()
        for field in field_list:
            result[field] = ''

        # update from db
        data = {
            'tt_user': tt_user,
            'tt_name': tt_name,
        }
        field_value_mapping = TT_Template.fetchCurrent(self.env, data)
        for k, v in field_value_mapping.items():
            if k in field_list:
                result[k] = v

        for field in field_list:
            field_type = self.config.get(self.SECTION_NAME, field + '.type',
                                         'text')
            field_value = field_value_mapping.get(field)
            field_detail = {
                'field_type': field_type,
                'field_value': field_value
            }
            result[field] = field_detail

        return result

    def _loadTemplateText(self, tt_name):
        """ get template text from tt_dict.
            return tt_text if found in db
                or default tt_text if exists
                or empty string if default not exists.
        """
        tt_text = TT_Template.fetch(self.env, tt_name)
        if not tt_text:
            tt_text = TT_Template.fetch(self.env, 'default')

        return tt_text

    def _sendResponse(self, req, message):
        """ send response and stop request handling
        """
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain' + ';charset=utf-8')
        req.send_header('Content-Length',
                        len(isinstance(message, unicode)
                        and message.encode('utf-8') or message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone

    def _saveTemplateText(self, tt_name, tt_text):
        """ save ticket template text to db.
        """
        id = TT_Template.insert(self.env, (int(time.time()), 'SYSTEM',
                                           tt_name, 'description', tt_text))
        return id

    def _getTicketTypeNames(self):
        """ get ticket type names
            return:
                ["defect", "enhancement", ..., "default"]
        """
        options = []

        ticket = Ticket(self.env)
        for field in ticket.fields:
            if field['name'] == 'type':
                options.extend(field['options'])

        options.extend(['default'])

        return options
