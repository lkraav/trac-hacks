# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Verigy (Singapore) Pte. Ltd.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import StringIO
import smtplib
import random
import re
import time
from datetime import datetime

from genshi.core import escape
from genshi.filters.html import HTMLSanitizer
from genshi.input import HTMLParser, ParseError
from trac.core import TracError, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.mimeview.api import Context, Mimeview
from trac.perm import IPermissionRequestor
from trac.util.datefmt import format_datetime, pretty_timedelta, utc
from trac.util.text import exception_to_unicode
from trac.web.api import HTTPBadRequest, IRequestHandler
from trac.web.chrome import web_context
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.formatter import Formatter, system_message

import wikiforms_lib


class WikiFormsMacro(WikiMacroBase):
    """Docs for WikiForms wiki processor.
    """
    implements(IEnvironmentSetupParticipant, IPermissionRequestor,
               IRequestHandler)

    # Database schema version (used to detect the need for upgrades).
    db_version = 1

    # Database schema
    db_schema = [
        Table('wikiforms_fields', key=('field'))[
            Column('field'),
            Column('value'),
            Column('updated_by'),
            Column('updated_on', type='INTEGER')
        ]
    ]

    placeholder_cnt = 0

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['WIKIFORMS_ADMIN', 'WIKIFORMS_UPDATE']

    # IEnvironmentSetupParticipant

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        db_version = self._get_database_version()
        if db_version is None:
            return True
        else:
            return int(db_version) < self.db_version

    def upgrade_environment(self, db=None):
        with self.env.db_transaction as db:
            # create tables according defined schema...
            db_manager = DatabaseManager(self.env).get_connector()[0]
            for tbl in self.db_schema:
                for sql in db_manager.to_sql(tbl):
                    db(sql)

            if self._get_database_version() is None:
                db("""
                    INSERT INTO system (name, value)
                    VALUES ('wikiforms_version', %s)
                    """, (self.db_version,))
            else:
                db("""
                    UPDATE system SET value = %s
                    WHERE name = 'wikiforms_version'
                    """, (self.db_version,))

    def _get_database_version(self):
        for value, in self.env.db_query("""
                SELECT value FROM system WHERE name='wikiforms_version'
                """):
            return value
        return None

    def match_request(self, req):
        return req.path_info == '/wikiforms/update'

    def process_request(self, req):
        try:
            # check whether user has form-update permissions...
            if 'WIKIFORMS_UPDATE' in req.perm or 'WIKIFORMS_ADMIN' in req.perm:
                pass
            else:
                msg = "You(%s) don't have enough permissions to update " \
                      "form values..." % req.authname
                raise TracError(msg)

            args = dict(req.args)
            #
            # you get something like this...
            #
            # {
            # '__BACKPATH'  : u'/trac/TPdev/wiki/sandbox',
            # '__FORM_TOKEN': u'28b12aa6e225d804bd863ec0',
            # '__SUBMIT'    : u'Commit',
            # '/wiki/sandbox/spec_comment': u'Please fill in your comment...',
            # '/wiki/sandbox/spec_completion': u'foo',
            # '/wiki/sandbox/spec_done': u'my_value',
            # '/wiki/sandbox/choose_one': u'val2',
            # '/wiki/sandbox/approval_comment': u'Please fill your\r\napproval\r\ncomment\r\nhere'
            # }
            #
            # self.log.debug(req.args)
            backpath = args.pop('__BACKPATH', None)
            args.pop('__FORM_TOKEN', None)
            args.pop('__SUBMIT', None)
            page = args.pop('__PAGE', None)
            notify_mailto = args.pop('__NOTIFY_MAILTO', None)
            notify_subject = args.pop('__NOTIFY_SUBJECT', None)
            notify_body = args.pop('__NOTIFY_BODY', None)

            if page is None:
                raise HTTPBadRequest('__PAGE is required')

            fields_to_be_stored = {}
            checkbox_state = {}
            unprocessed = {}

            # first step : extract hidden fields to find all checkboxes...
            for name, value in args.iteritems():
                m = re.match('^hidden_(.+)$', name)

                if m is not None:
                    # there is a checkbutton...
                    checkbox_name = m.group(1)
                    checkbox_state[checkbox_name] = value
                else:
                    unprocessed[name] = value

            # process checkboxes first (as they have a different logic)...
            # an unchecked checkbox has no response => the absence of a
            # response has to be interpreted as 'off'.
            # In addition, even for checkboxes in 'on' state nothing is
            # responded if they're disabled (read-only)...
            for name, state in checkbox_state.iteritems():
                if state == 'enabled_off':
                    # checkbox was 'off' at time when form was rendered.
                    # => the only possible transition is to 'on'
                    if name in unprocessed:
                        # state change ('off' -> 'on') => update database...
                        fields_to_be_stored[name] = unprocessed[name]
                elif state == 'enabled_on':
                    # checkbox was 'on' at time when form was rendered.
                    # => the only possible transition is to 'off'
                    if name not in unprocessed:
                        # interprete no response as 'off'...
                        # state change ('on' -> 'off') => update database...
                        fields_to_be_stored[name] = ''

            # third step : process all non-checkbox fields...
            for name, value in unprocessed.iteritems():
                if name not in checkbox_state and \
                        isinstance(value, basestring):
                    # it's not a checkbox...
                    # might be compared against current database state to log
                    # changes, only...
                    fields_to_be_stored[name] = value

            # store all values in database...
            authname = req.authname
            for name, value in fields_to_be_stored.iteritems():
                value = re.sub('(\r\n|\r|\n)', '\\\\n', value)

                self.set_tracform_field(name, value, authname)

            # set form modification date...
            self.set_tracform_field(page, '', authname)

            if notify_mailto is not None:

                if self.config.get('notification', 'smtp_enabled'):
                    smtp_from = self.config.get('notification', 'smtp_from')
                    smtp_to = notify_mailto.split(",")
                    smtp_msg = []

                    smtp_msg.append("From:    %s" % smtp_from)
                    smtp_msg.append("To:      %s" % ", ".join(smtp_to))
                    smtp_msg.append("Subject: %s" % notify_subject)
                    smtp_msg.append("")

                    smtp_msg.append("Hello,")
                    smtp_msg.append("")
                    smtp_msg.append("please note that form '%s' was updated "
                                    "by user '%s'." % (page, req.authname))

                    if backpath is not None:
                        smtp_msg.append("")
                        smtp_msg.append("Link : %s%s" % (
                            self.config.get('trac', 'base_url'), backpath))

                    smtp_msg.append("")
                    smtp_msg.append("Value(s) of field(s) in the form are:")

                    rows = self.get_tracform()

                    regexp = re.compile("%s\/(.*)" % page)

                    for row in rows:
                        m = regexp.match(row['field'])
                        if m:
                            smtp_msg.append("  %-15s : %s" %
                                            (m.group(1), row['value']))

                    if notify_body is not None:
                        smtp_msg.append("")
                        smtp_msg.append("Custom information follows:")
                        smtp_msg.append(notify_body)

                    smtp_server = smtplib.SMTP('localhost')
                    smtp_server.sendmail(
                        smtp_from, smtp_to, "\r\n".join(smtp_msg))
                    smtp_server.quit()

            if backpath is not None:
                # req.redirect(backpath)
                req.send_response(302)
                req.send_header('Content-type', 'text/plain')
                req.send_header('Location', backpath)
                req.send_header('Content-Length', 2)
                req.end_headers()
                req.write('OK')
            else:
                req.send_response(200)
                req.send_header('Content-type', 'text/plain')
                req.send_header('Content-Length', 2)
                req.end_headers()
                req.write('OK')
        except Exception, e:
            etb = exception_to_unicode(e, traceback=True).encode('utf-8')
            req.send_response(500)
            req.send_header('Content-type', 'text/plain')
            req.send_header('Content-Length', len(etb))
            req.end_headers()
            self.log.warning("Failed processing request for %s: "
                             "%s", req.path_info, etb)
            req.write(etb)

    def expand_macro(self, formatter, name, args):
        # set defaults...
        page = formatter.req.path_info
        context = ''

        formatter.req.send_header('Pragma', 'no-cache')
        formatter.req.send_header('Cache-Control', 'no-cache')
        formatter.req.send_header('Cache-Control', 'must-revalidate')
        formatter.req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')

        # parse request...
        unprocessed = args
        result = ''
        final_html = {}
        permission = {'r': True, 'w': True}
        permission_alias = {}

        tags = [
            {'start': '<tf>', 'end': '</tf>'},
            {'start': '<f>', 'end': '</f>'}
        ]

        while unprocessed != '':
            # search for start-of-tag...
            start_tag_idx = -1
            for tag in tags:
                idx = unprocessed.find(tag['start'])
                if (idx >= 0):
                    if (start_tag_idx == -1 or idx < start_tag_idx):
                        start_tag_idx = idx
                        start_tag = tag['start']
                        end_tag = tag['end']

            if start_tag_idx >= 0:
                # start-tag found...
                # search for end-tag...
                end_tag_idx = unprocessed.find(end_tag)

                if end_tag_idx >= 0:
                    # start-tag and end-tag found...
                    if permission['r']:
                        # part before start-tag...
                        result += unprocessed[0: start_tag_idx]
                    # part between start- and end-tag...
                    tag = unprocessed[start_tag_idx +
                                      len(start_tag): end_tag_idx]
                    # part including start- and end-tag...
                    full_tag = unprocessed[
                        start_tag_idx: end_tag_idx + len(end_tag)]
                    # part after end-tag...
                    unprocessed = unprocessed[end_tag_idx + len(end_tag):]

                    tag = re.sub('#[^\n\f]*', '', tag)  # strip comments...

                    command, options = wikiforms_lib.get_piece(tag)

                    if command == 'context':
                        # set context to...
                        context, ignored = wikiforms_lib.get_piece(options)
                    elif command == 'value':
                        # get value of...
                        name, ignored = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)

                        entry = self.get_tracform_field(resolved_name)
                        if permission['r']:
                            result += "%s" % entry['value']
                    elif command == 'permission':
                        # get/set permission...
                        sub_command, remainder = \
                            wikiforms_lib.get_piece(options, [':'])

                        if sub_command == 'alias':
                            alias_name, ignored = \
                                wikiforms_lib.get_piece(remainder, [' '])

                            if alias_name in permission_alias:
                                # fetch already defined permission setup...
                                permission['r'] = \
                                    permission_alias[alias_name]['r']
                                permission['w'] = \
                                    permission_alias[alias_name]['w']
                            else:
                                # create alias for current permission setup...
                                permission_alias[alias_name] = {
                                    'r': permission['r'],
                                    'w': permission['w']
                                }
                        elif sub_command == 'show':
                            result += 'current permission is ('
                            if permission['r']:
                                result += 'r'

                            if permission['w']:
                                result += 'w'

                            result += ')'
                        elif sub_command == 'change':
                            permission_action, permission_condition = \
                                wikiforms_lib.get_piece(remainder, [':'])

                            if permission_condition != '':
                                condition, msg = \
                                    self.resolve_permission(permission_condition, formatter)

                                if msg != '':
                                    return system_message(msg)
                            else:
                                condition = True

                            if condition:
                                if permission_action in \
                                        ['r', 'rw', '+r', '+rw', '+r-w', '+r+w']:
                                    permission['r'] = True
                                elif permission_action in \
                                        ['', 'w', '-r', '-rw', '-r-w', '-r+w']:
                                    permission['r'] = False
                                if permission_action in \
                                        ['w', 'rw', '+w', '+rw', '-r+w', '+r+w']:
                                    permission['w'] = True
                                elif permission_action in \
                                        ['', 'r', '-w', '-rw', '+r-w', '-r-w']:
                                    permission['w'] = False
                        else:
                            return system_message("unknown sub-command '%s' "
                                                  "of command '%s'"
                                                  % (sub_command, command))

                    elif command == 'values':
                        # get value of...
                        local_context, parameters = \
                            wikiforms_lib.get_piece(options)

                        while (parameters != ''):
                            m = re.match('(.*?)<(\S+?)>(.*)$', parameters)
                            if (m is not None):
                                if permission['r']:
                                    result += m.group(1)
                                name = m.group(2)
                                parameters = m.group(3)

                                resolved_name = self.resolve_name(
                                    page, local_context, name)
                                entry = self.get_tracform_field(resolved_name)
                                if permission['r']:
                                    result += "%s" % entry['value']
                            else:
                                if permission['r']:
                                    result += parameters
                                parameters = ''

                    elif command == 'who':
                        # get updated_by of...
                        name, ignored = wikiforms_lib.get_piece(options)

                        resolved_name = self.resolve_name(page, context, name)
                        entry = self.get_tracform_field(resolved_name)
                        if permission['r']:
                            result += "%s" % entry['updated_by']

                    elif command == 'when':
                        # get updated_on of...
                        name, ignored = wikiforms_lib.get_piece(options)

                        resolved_name = self.resolve_name(page, context, name)
                        entry = self.get_tracform_field(resolved_name)
                        if permission['r']:
                            result += "%s" \
                                      % self.to_timestring(entry['updated_on'])

                    elif command == 'when2':
                        # get updated_on of...
                        name, ignored = wikiforms_lib.get_piece(options)

                        resolved_name = self.resolve_name(page, context, name)
                        entry = self.get_tracform_field(resolved_name)

                        if permission['r']:
                            if entry['field'] is not None:
                                last_modified = \
                                    datetime.fromtimestamp(entry['updated_on'],
                                                           utc)
                                now = datetime.now(utc)
                                pretty_delta = \
                                    pretty_timedelta(now, last_modified)
                            else:
                                pretty_delta = 'unset-time'
                            result += "%s, %s ago" \
                                      % (self.to_timestring(entry['updated_on']),
                                         pretty_delta)

                    elif command == 'lastmodified':
                        # get updated_on,updated_by of...
                        name, ignored = wikiforms_lib.get_piece(options)

                        resolved_name = self.resolve_name(page, context, name)
                        entry = self.get_tracform_field(resolved_name)

                        now = datetime.now(utc)

                        req = formatter.req
                        if (entry['field'] is not None):
                            last_modified = \
                                datetime.fromtimestamp(
                                    entry['updated_on'], utc)
                            pretty_delta = pretty_timedelta(now, last_modified)
                            time_string = format_datetime(last_modified,
                                                          '%a %b %d %T %Y %Z',
                                                          req.tz, req.locale)
                        else:
                            time_string = self.to_timestring(
                                entry['updated_on'])
                            pretty_delta = 'unset-time'

                        if permission['r']:
                            result += "'''Last Modified:''' %s (%s ago) " \
                                      "by %s" % (time_string, pretty_delta,
                                                 entry['updated_by'])

                    elif command == 'set':
                        # set value of...
                        name, value = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)
                        authname = formatter.req.authname
                        self.set_tracform_field(resolved_name, value, authname)

                    elif command == 'dump':
                        # dump fields...
                        name, ignored = wikiforms_lib.get_piece(options)
                        rows = self.get_tracform()

                        if permission['r']:
                            result += "||'''field'''||'''value'''||'''who'''||'''when'''\n"
                        for row in rows:
                            m = re.search(name, row['field'])
                            if m:
                                if permission['r']:
                                    result += "||%s||%s||%s||%s\n" \
                                              % (row['field'],
                                                 re.sub('\n', '\\\\n',
                                                        row['value']),
                                                 row['updated_by'],
                                                 row['updated_on'])

                    elif command == 'delete':
                        # delete a field...
                        formatter.req.perm.require('WIKIFORMS_ADMIN')
                        name, ignored = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)
                        self.delete_tracform_field(resolved_name)

                    elif command == 'checkbox':
                        # create checkbox...
                        name, parameters = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)

                        placeholder_id = self.get_placeholder_id()
                        result += placeholder_id

                        final_html[placeholder_id] = \
                            self.create_checkbox(name, resolved_name,
                                                 parameters, placeholder_id,
                                                 permission)

                    elif command == 'radio':
                        # create radio...
                        name, parameters = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)

                        placeholder_id = self.get_placeholder_id()
                        result += placeholder_id

                        final_html[placeholder_id] = \
                            self.create_radio(name, resolved_name,
                                              parameters, placeholder_id,
                                              permission)

                    elif command == 'input':
                        # create input...
                        name, parameters = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)

                        placeholder_id = self.get_placeholder_id()
                        result += placeholder_id

                        final_html[placeholder_id] = \
                            self.create_input(name, resolved_name,
                                              parameters, placeholder_id,
                                              permission)

                    elif command == 'textarea':
                        # create text...
                        name, parameters = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)

                        placeholder_id = self.get_placeholder_id()
                        result += placeholder_id

                        final_html[placeholder_id] = \
                            self.create_textarea(name, resolved_name,
                                                 parameters, placeholder_id,
                                                 permission)

                    elif command == 'select':
                        # create select...
                        name, parameters = wikiforms_lib.get_piece(options)
                        resolved_name = self.resolve_name(page, context, name)

                        placeholder_id = self.get_placeholder_id()
                        result += placeholder_id

                        final_html[placeholder_id] = \
                            self.create_select(name, resolved_name,
                                               parameters, placeholder_id,
                                               permission)

                    elif command == 'notify':
                        # create notify...
                        resolved_name = self.resolve_name(page, context, '')

                        placeholder_id = self.get_placeholder_id()
                        result += placeholder_id

                        final_html[placeholder_id] = \
                            self.create_notify('', resolved_name,
                                               options, placeholder_id)

                    elif command == 'submit':
                        # create button...

                        placeholder_id = self.get_placeholder_id()
                        result += placeholder_id
                        resolved_name = self.resolve_name(page, context, name)

                        final_html[placeholder_id] = \
                            self.create_submit(name, resolved_name, options,
                                               placeholder_id, permission)
                    else:
                        # unknown command => echo original description
                        # including tags around...
                        if permission['r']:
                            result += full_tag
                else:
                    # start-tag but no end-tag found...
                    if permission['r']:
                        result += unprocessed
                    unprocessed = ''

            else:
                # no start-tag found...
                if permission['r']:
                    result += unprocessed
                unprocessed = ''

        # wikify structure of document...
        result = self.wiki_to_html(formatter, result)

        # fill in final html for placeholders...
        for placeholder_id, placeholder_value in final_html.iteritems():
            result = re.sub(placeholder_id, placeholder_value, result, 1)

        return ''.join(self.build_form(formatter, page, result))

    def create_checkbox(self, name, resolved_name, parameters, placeholder_id,
                        permission):
        # create checkbox...
        result = ''
        checkbox_def = {
            'cfg': {
                'name': resolved_name,
                'checked': False,
                'value': 'true',
                'class': 'checkbox_css_class',
                'id': 'checkbox_css_id',
                'debug': False
            },
            'xtras': [],
            'xtra': {},
        }

        # ...overwrite hardcoded defaults with user-defined values...
        checkbox_def = wikiforms_lib.parse_options(parameters, checkbox_def)

        # fetch state from database...
        entry = self.get_tracform_field(resolved_name)

        if (entry['field'] is not None):
            # derive checked-state from database...
            checkbox_def['cfg']['checked'] = (
                entry['value'] == checkbox_def['cfg']['value'])
        else:
            checkbox_def['cfg']['checked'] = self.to_boolean(
                checkbox_def['cfg']['checked'])

        if checkbox_def['cfg']['debug']:
            result += "debug: parameters=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s< perm=>%s<" \
                      % (parameters,
                         name, resolved_name,
                         str(checkbox_def['cfg']),
                         str(checkbox_def['xtras']),
                         str(checkbox_def['xtra']),
                         str(entry), permission)

        # map flag to html needs...
        hidden_value = ""

        if not permission['w']:
            access_flag = 'DISABLED'
            hidden_value = 'disabled'
        else:
            access_flag = ''
            hidden_value = 'enabled'

        if checkbox_def['cfg']['checked']:
            checkbox_def['cfg']['checked'] = 'checked="checked"'
            hidden_value += '_on'
        else:
            checkbox_def['cfg']['checked'] = ''
            hidden_value += '_off'

        # when submitting the form, checked checkboxes are transmitted, only.
        # => the update-processor will not know about unchecked ones.
        # => send a hidden field for all checkboxes to allow to find those.
        if permission['r']:
            result += """
                <INPUT type='checkbox' name='%s' id='%s' class='%s' value='%s' %s %s>
                """ % (checkbox_def['cfg']['name'   ],
                       checkbox_def['cfg']['id'],
                       checkbox_def['cfg']['class'],
                       checkbox_def['cfg']['value'],
                       checkbox_def['cfg']['checked'],
                       access_flag)

        result += """
            <INPUT type="hidden" name='hidden_%s' value='%s'>
            """ % (checkbox_def['cfg']['name'], hidden_value)

        return result

    def create_radio(self, name, resolved_name, parameters, placeholder_id,
                     permission):
        # create radio...
        result = ''
        radio_def = {
            'cfg': {
                'name': resolved_name,
                'checked': False,
                'value': 'true',
                'class': 'radio_css_class',
                'id': 'radio_css_id',
                'debug': False
            },
            'xtras': [],
            'xtra': {},
        }

        # ...overwrite hardcoded defaults with user-defined values...
        radio_def = wikiforms_lib.parse_options(parameters, radio_def)

        # fetch state from database...
        entry = self.get_tracform_field(resolved_name)

        if entry['field'] is not None:
            # derive checked-state from database...
            radio_def['cfg']['checked'] = (
                entry['value'] == radio_def['cfg']['value'])
        else:
            radio_def['cfg']['checked'] = self.to_boolean(
                radio_def['cfg']['checked'])

        if (radio_def['cfg']['debug']):
            result += "debug: parameters=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s< perm=>%s<" \
                % (parameters,
                   name, resolved_name,
                   str(radio_def['cfg']),
                   str(radio_def['xtras']),
                   str(radio_def['xtra']),
                   str(entry), permission)

        # map flag to html needs...
        if radio_def['cfg']['checked']:
            radio_def['cfg']['checked'] = 'checked="checked"'
        else:
            radio_def['cfg']['checked'] = ''

        if not permission['w']:
            access_flag = 'DISABLED'
        else:
            access_flag = ''

        if permission['r']:
            result += """
                <INPUT type='radio' name='%s' id='%s' class='%s' value='%s' %s %s >
                """ % (radio_def['cfg']['name'],
                       radio_def['cfg']['id'],
                       radio_def['cfg']['class'],
                       radio_def['cfg']['value'],
                       radio_def['cfg']['checked'],
                       access_flag)
        return result

    def create_input(self, name, resolved_name, parameters, placeholder_id,
                     permission):
        # create input...
        result = ''
        input_def = {
            'cfg': {
                'name': resolved_name,
                'value': '',
                'size': 22,
                'class': 'input_css_class',
                'id': 'input_css_id',
                'debug': False,
            },
            'xtras': [],
            'xtra': {},
        }

        # ...overwrite hardcoded defaults with user-defined values...
        input_def = wikiforms_lib.parse_options(parameters, input_def)

        # fetch state from database...
        entry = self.get_tracform_field(resolved_name)

        if input_def['cfg']['debug']:
            result += "debug: parameters=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s< perm=>%s<" \
                      % (parameters,
                         name, resolved_name,
                         str(input_def['cfg']),
                         str(input_def['xtras']),
                         str(input_def['xtra']),
                         str(entry), permission)

        if entry['field'] is not None:
            # ...overwrite hardcoded/user-defined default with database value.
            input_def['cfg']['value'] = entry['value']

        if not permission['w']:
            access_flag = 'DISABLED'
        else:
            access_flag = ''

        if permission['r']:
            result += """
                <INPUT name='%s' id='%s' class='%s' value='%s' size=%s %s >
                """ % (input_def['cfg']['name'],
                       input_def['cfg']['id'],
                       input_def['cfg']['class'],
                       self.to_quote(input_def['cfg']['value']),
                       input_def['cfg']['size'],
                       access_flag)
        return result

    def create_textarea(self, name, resolved_name, parameters, placeholder_id,
                        permission):
        # create text...
        result = ''
        text_def = {
            'cfg': {
                'name': resolved_name,
                'cols': 10,
                'rows': 2,
                'value': '',
                'class': 'text_css_class',
                'id': 'text_css_id',
                'debug': False
            },
            'xtras': [],
            'xtra': {}
        }

        # ...overwrite hardcoded defaults with user-defined values...
        text_def = wikiforms_lib.parse_options(parameters, text_def)

        # fetch state from database...
        entry = self.get_tracform_field(resolved_name)

        if text_def['cfg']['debug']:
            result += "debug: parameters=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s< perm=>%s<" \
                      % (parameters,
                         name, resolved_name,
                         str(text_def['cfg']),
                         str(text_def['xtras']),
                         str(text_def['xtra']),
                         str(entry), permission)

        if entry['field'] is not None:
            # ...overwrite hardcoded/user-defined default with database value.
            text_def['cfg']['value'] = entry['value']

        if not permission['w']:
            access_flag = 'DISABLED'
        else:
            access_flag = ''

        if permission['r']:
            result += """
                <TEXTAREA name='%s' id='%s' class='%s' cols='%s' rows='%s' %s >%s</TEXTAREA>
                """ % (text_def['cfg']['name' ],
                       text_def['cfg']['id'],
                       text_def['cfg']['class'],
                       text_def['cfg']['cols'],
                       text_def['cfg']['rows'],
                       access_flag,
                       escape(text_def['cfg']['value']))
        return result

    def create_select(self, name, resolved_name, parameters, placeholder_id,
                      permission):
        # create select...
        result = ''
        select_def = {
            'cfg': {
                'name': resolved_name,
                'default': None,
                'class': 'select_css_class',
                'id': 'select_css_id',
                'debug': False
            },
            'xtras': [],
            'xtra': {}
        }

        # ...overwrite hardcoded defaults with user-defined values...
        select_def = wikiforms_lib.parse_options(parameters, select_def)

        # fetch state from database...
        entry = self.get_tracform_field(resolved_name)

        if (select_def['cfg']['debug']):
            result += "debug: parameters=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s< perm=>%s<" \
                      % (parameters,
                         name, resolved_name,
                         str(select_def['cfg']),
                         str(select_def['xtras']),
                         str(select_def['xtra']),
                         str(entry), permission)

        if not permission['w']:
            access_flag = 'DISABLED'
        else:
            access_flag = ''

        option_section = ''
        for option in select_def['xtras']:
            if select_def['xtra'][option] == '':
                value = option
                label = option
            else:
                value = option
                label = select_def['xtra'][option]

            selected = False

            if select_def['cfg']['default'] is not None:
                selected = (value == select_def['cfg']['default'])

            if entry['field'] is not None:
                selected = value == entry['value']

            # map flag to html needs...
            if selected:
                selected = 'selected'
            else:
                selected = ''

            option_section += """
                <OPTION value='%s' %s>%s</OPTION>
                """ % (self.to_quote(value), selected, label)

        if permission['r']:
            result += """
                <SELECT name='%s' id='%s' class='%s' %s>%s</SELECT>
                """ % (select_def['cfg']['name'],
                       select_def['cfg']['id'],
                       select_def['cfg']['class'],
                       access_flag,
                       option_section)
        return result

    def create_notify(self, name, resolved_name, parameters, placeholder_id):
        # create notify...
        result = ''
        notify_def = {
            'cfg': {
                'mail_to': 'default_receiver',
                'subject': 'wikiform updated',
                'body': None
            },
            'xtras': [],
            'xtra': {}
        }

        # ...overwrite hardcoded defaults with user-defined values...
        notify_def = wikiforms_lib.parse_options(parameters, notify_def)

        result += """
            <INPUT type="hidden" name="__NOTIFY_MAILTO" value="%s">
            """ % notify_def['cfg']['mail_to']

        result += """
            <INPUT type="hidden" name="__NOTIFY_SUBJECT" value="%s">
            """ % notify_def['cfg']['subject']

        if notify_def['cfg']['body'] is not None:
            result += """
                <INPUT type="hidden" name="__NOTIFY_BODY" value="%s">
                """ % notify_def['cfg']['body']

        return result

    def create_submit(self, name, resolved_name, parameters, placeholder_id,
                      permission):
        # create submit...
        result = ''
        button_def = {
            'cfg': {
                'label': 'Send',
                'class': 'buttons',
                'id': 'button_css_id',
                'debug': False
            },
            'xtras': [],
            'xtra': {}
        }

        button_def = wikiforms_lib.parse_options(parameters, button_def)

        if button_def['cfg']['debug']:
            result += "debug: parameters=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s< perm=>%s<" \
                % (parameters,
                   name, resolved_name,
                   str(button_def['cfg']),
                   str(button_def['xtras']),
                   str(button_def['xtra']),
                   permission)

        if not permission['w']:
            access_flag = 'DISABLED'
        else:
            access_flag = ''

        if permission['r']:
            result += """
                <INPUT type='submit' name='__SUBMIT' id='%s' class='%s' value='%s' %s >
                """ % (button_def['cfg']['id'],
                       button_def['cfg']['class'],
                       button_def['cfg']['label'],
                       access_flag)
        return result

    def build_form(self, formatter, page, form_body):
        form_name = 'form_name'
        form_css_id = 'form_css_id'
        form_css_class = 'form_css_class'
        dest = str(formatter.req.href('/wikiforms/update'))
        backpath = str(formatter.req.href(formatter.req.path_info))
        form_token = str(formatter.req.form_token)

        yield """
                 <FORM
                  class="printableform"
                  method="POST"
                  action=%s
                  name="%s"
                  id="%s"
                  class="%s"
                 >

                 %s

                 <INPUT
                  type="hidden"
                  name="__BACKPATH"
                  value=%s
                 >

                 <INPUT
                  type="hidden"
                  name="__FORM_TOKEN"
                  value=%s
                 >

                 <INPUT
                  type="hidden"
                  name="__PAGE"
                  value='%s'
                 >

                 </FORM>
              """ % (dest, form_name, form_css_id, form_css_class,
                     form_body, backpath, form_token, page)

    def to_quote(self, value):
        if value is None:
            result = ''
        else:
            result = value
            result = re.sub("'", "&#39;", result)
        return result

    def to_unquote(self, value):
        if value is None:
            result = ''
        else:
            result = value
            result = re.sub("&#39;", "'", result)

        return result

    def to_timestring(self, time_int, format='%Y-%b-%d %H:%M:%S'):
        if time_int is None:
            result = 'unset-time'
        else:
            result = time.strftime(format, time.localtime(time_int))

        return result

    def to_userstring(self, user):
        if user is None:
            result = 'unset-user'
        else:
            result = user

        return result

    def get_tracform_field(self, resolved_name):
        result = {
            'field': None,
            'value': '',
            'updated_by': self.to_userstring(None),
            'updated_on': None
        }
        row = []

        for field, value, updated_by, updated_on in self.env.db_query("""
                SELECT field,value,updated_by,updated_on
                FROM wikiforms_fields
                WHERE field=%s
                """, (resolved_name,)):
            row.append({
                'field': self.to_unquote(field),
                'value': self.to_unquote(value),
                'updated_by': self.to_userstring(updated_by),
                'updated_on': updated_on
            })

        if len(row) == 1:
            result = row[0]

        return result

    def get_tracform(self):
        result = []

        for field, value, updated_by, updated_on in self.env.db_query("""
                SELECT field,value,updated_by,updated_on
                FROM wikiforms_fields
                """):
            result.append({
                'field': self.to_unquote(field),
                'value': self.to_unquote(value),
                'updated_by': updated_by,
                'updated_on': self.to_timestring(updated_on)
            })

        return result

    def set_tracform_field(self, resolved_name, value, authname):
        updated_on = int(time.time())
        updated_by = authname

        with self.env.db_transaction as db:
            row = None
            for row in db("""
                    SELECT value
                    FROM wikiforms_fields
                    WHERE field=%s
                    """, (resolved_name,)):
                if self.to_quote(value) != row[0]:
                    # new value => update...
                    db("""
                        UPDATE wikiforms_fields
                        SET value=%s, updated_on=%s, updated_by=%s
                        WHERE field=%s
                        """, (value, updated_on, updated_by, resolved_name))
                break
            else:
                # does not exist => insert...
                db("""
                    INSERT INTO wikiforms_fields
                      (field,value,updated_on,updated_by)
                    VALUES (%s, %s, %s, %s)
                    """, (resolved_name, value, updated_on, updated_by))

    def delete_tracform_field(self, resolved_name):
        self.env.db_transaction("""
            DELETE FROM wikiforms_fields
            WHERE field=%s
            """, (resolved_name,))

    def get_placeholder_id(self):
        WikiFormsMacro.placeholder_cnt += 1
        return "CNT/%s/:VAL/%s/" % (WikiFormsMacro.placeholder_cnt,
                                    random.randint(0, 1000000000))

    def wiki_to_html(self, formatter, text):
        out = StringIO.StringIO()
        Formatter(formatter.env, formatter.context).format(text, out)
        return out.getvalue()

    def resolve_name(self, page, context, name):
        result = page

        if name != '':
            if context != '':
                if context[0] == '/':
                    # absolute context...
                    result = context
                else:
                    # relative context...
                    result += '/' + context

            if name[0] == '/':
                # absolute name...
                result = name
            else:
                # relative name...
                result += '/' + name

        return result

    def to_boolean(self, value):
        if value is not None:
            if isinstance(value, (bool)):
                result = value
            elif value.lower() in ['1', 'true', 'on', 'yes']:
                result = True
            else:
                result = False
        else:
            result = False

        return result

    def resolve_permission(self, permission_condition, formatter):
        result = None
        msg = ''

        lhs, rest_of_line = wikiforms_lib.get_piece(
            permission_condition, [' '])

        if lhs == 'user':
            LHS = formatter.req.authname
            operator, rhs = wikiforms_lib.get_piece(rest_of_line, [' '])

        elif lhs == 'ticket_state':
            ticket_id, rest_of_line = wikiforms_lib.get_piece(
                rest_of_line, [' '])
            operator, rhs = wikiforms_lib.get_piece(rest_of_line, [' '])
            for status, in self.env.db_query("""
                    SELECT status FROM ticket WHERE id=%s
                    """, (ticket_id,)):
                LHS = status
                break
            else:
                msg += 'Ticket(%s) does not exist' % (ticket_id)

        elif lhs == 'milestone_is_complete':
            milestone_name, ignored = \
                wikiforms_lib.get_piece(rest_of_line, [' '])

            for completed, in self.env.db_query("""
                    SELECT completed FROM milestone WHERE name=%s
                    """, (milestone_name,)):
                if completed > 0:
                    LHS = '1'
                else:
                    LHS = '0'
                operator = 'in'
                rhs = '1'
                break
            else:
                msg += 'Milestone(%s) does not exist' % milestone_name
        else:
            LHS = lhs
            operator, rhs = wikiforms_lib.get_piece(rest_of_line, [' '])

        if msg == '':
            RHS = []

            while rhs != '':
                tmp, rhs = wikiforms_lib.get_piece(rhs, [','])
                RHS.append(tmp)

            if operator == 'in':
                if LHS in RHS:
                    result = True
                else:
                    result = False
            elif operator == 'not_in':
                if LHS not in RHS:
                    result = True
                else:
                    result = False
            else:
                msg += 'Operator(%s) is not yet supported' % (operator)

        return result, msg


class WikiFormIncludeMacro(WikiMacroBase):
    """
    A macro to include wiki forms (wiki pages) with optional parameters.
    """

    # the following stuff is a stripped down and adapted version of
    # IncludeMacro.
    def expand_macro(self, formatter, name, args):
        wikiforms_page, args = wikiforms_lib.get_piece(args)

        if wikiforms_page == "":
            return system_message('Invalid(empty) argument')

        parameters = {
            'cfg': {},
            'xtras': [],
            'xtra': {}
        }

        parameters = wikiforms_lib.parse_options(args, parameters)

        formatter.req.perm.require('WIKI_VIEW')
        page = WikiPage(self.env, wikiforms_page)
        if page.exists is False:
            return system_message("Can't include non existing WikiForm(%s)"
                                  % wikiforms_page)

        out = page.text
        ctxt = web_context(formatter.req, page.resource)

        # replace defined keys...
        for key in parameters['xtras']:
            out = re.sub('\{\{\s*' + key + '\s*\}\}',
                         parameters['xtra'][key], out)

        out = Mimeview(self.env).render(ctxt, 'text/x-trac-wiki', out)

        # Escape if needed
        if not self.config.getbool('wiki', 'render_unsafe_content', False):
            buf = StringIO.StringIO(out)
            try:
                out = HTMLParser(buf).parse() | HTMLSanitizer()
            except ParseError:
                out = escape(out)

        return out
