# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2011-2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.config import BoolOption, ListOption
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.web.api import IRequestFilter


class SimpleTicketModule(Component):
    """A request filter to implement the SimpleTicket reduced ticket
    entry form."""
    implements(IPermissionRequestor, IRequestFilter)

    fields = ListOption('simpleticket', 'fields', default='',
                        doc="""Fields to hide for the simple ticket entry
                               form.""")

    show_only = BoolOption('simpleticket', 'show_only', default=False,
                           doc="""If True, show only the specified fields
                                  rather than hiding the specified fields""")

    required_fields = set(['summary', 'reporter', 'owner',
                           'description', 'type', 'status'])

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield 'TICKET_CREATE_SIMPLE', ['TICKET_CREATE']

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template is not None and data is not None and \
                req.path_info.startswith('/newticket') and \
                'fields' in data and \
                data['fields'] is not None:
            if 'TICKET_CREATE_SIMPLE' in req.perm and \
                    'TRAC_ADMIN' not in req.perm:
                self.log.debug('SimpleTicket: Filtering new ticket form '
                               'for %s', req.authname)
                if self.show_only:
                    fields = set(self.fields) | self.required_fields
                    data['fields'] = [f for f in data['fields']
                                      if f is not None and 'name' in f and
                                      f['name'] in fields]
                else:
                    fields = set(self.fields) - self.required_fields
                    data['fields'] = [f for f in data['fields']
                                      if f is not None and 'name' in f and
                                      f['name'] not in fields]

        return template, data, content_type
