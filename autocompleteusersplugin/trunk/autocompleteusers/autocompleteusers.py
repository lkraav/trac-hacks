# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.config import ListOption
from trac.core import Component, implements
from trac.util.text import obfuscate_email_address
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import Chrome, ITemplateProvider
from trac.web.chrome import add_script, add_script_data, add_stylesheet


USER = 0
NAME = 1
EMAIL = 2  # indices

SECTION_NAME = 'autocomplete'
FIELDS_OPTION = 'fields'
SCRIPT_FIELD_NAME = 'autocomplete_fields'


class AutocompleteUsers(Component):
    implements(IRequestFilter, IRequestHandler, ITemplateProvider)

    complement_fields = ListOption(
        SECTION_NAME, FIELDS_OPTION, default='',
        doc="select fields to autocomplement")

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.rstrip('/') == '/subjects'

    def process_request(self, req):

        subjects = []
        if req.args.get('users', '1') == '1':
            users = self._get_users(req)
            subjects = ['%s|%s|%s' % (user[USER],
                                      user[EMAIL] and '<%s> ' % user[EMAIL] or '',
                                      user[NAME])
                        for value, user in users]  # value unused (placeholder needed for sorting)

        if req.args.get('groups'):
            groups = self._get_groups(req)
            if groups:
                subjects.extend(['%s||group' % group for group in groups])

        req.send('\n'.join(subjects).encode('utf-8'), 'text/plain')

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename

        return [('autocomplete', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('ticket.html', 'admin_perms.html', 'query.html'):
            add_stylesheet(req, 'autocomplete/css/autocomplete.css')
            add_script(req, 'autocomplete/js/autocomplete.js')
            add_script(req, 'autocomplete/js/format_item.js')

            custom_fields = self.config.getlist(SECTION_NAME, FIELDS_OPTION)
            script_data = {SCRIPT_FIELD_NAME: custom_fields}

            if template == 'ticket.html':
                add_script(req, 'autocomplete/js/autocomplete_ticket.js')
                script_data.update({
                    'newticket': req.path_info.rstrip() == '/newticket'
                })
            elif template == 'admin_perms.html':
                add_script(req, 'autocomplete/js/autocomplete_perms.js')
            elif template == 'query.html':
                add_script(req, 'autocomplete/js/autocomplete_query.js')

            add_script_data(req, script_data)

        return template, data, content_type

    # Private methods

    def _get_groups(self, req):
        # Returns a list of groups by filtering users with session data
        # from the list of all subjects. This has the caveat of also
        # returning users without session data, but there currently seems
        # to be no other way to handle this.
        query = req.args.get('q', '').lower()
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT DISTINCT username FROM permission")
        perm_users = [row[0] for row in cursor]
        known_users = set(item[0] for item in self.env.get_known_users())
        return sorted(user for user in perm_users
                      if user not in known_users and
                      user.lower().startswith(query))

    def _get_users(self, req):
        # instead of known_users, could be
        # perm = PermissionSystem(self.env)
        # owners = perm.get_users_with_permission('TICKET_MODIFY')
        # owners.sort()
        # see: http://trac.edgewall.org/browser/trunk/trac/ticket/default_workflow.py#L232

        query = req.args.get('q', '').lower()

        # user names, email addresses, full names
        can_view = Chrome(self.env).show_email_addresses or \
            'EMAIL_VIEW' in req.perm
        users = []
        for user_data in self.env.get_known_users():
            user_data = [value or '' for value in user_data]
            if not can_view and user_data[EMAIL]:
                user_data[EMAIL] = obfuscate_email_address(user_data[EMAIL])
            for index, field in enumerate((USER, EMAIL, NAME)):  # ordered by how they appear
                value = user_data[field].lower()

                if value.startswith(query):
                    users.append((2 - index, user_data))  # 2-index is the sort key
                    break
                if field == NAME:
                    lastnames = value.split()[1:]
                    if sum(name.startswith(query) for name in lastnames):
                        users.append((2 - index, user_data))  # 2-index is the sort key
                        break

        return sorted(users)
