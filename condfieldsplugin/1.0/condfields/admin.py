# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac import ticket
from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.ticket.api import TicketSystem

from customfieldadmin.api import CustomFields


class CondFieldsAdmin(Component):

    implements(IAdminPanelProvider)

    ### IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'typecondfields',
                   'Ticket Type Fields')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TICKET_ADMIN')

        if req.method == 'POST':
            self._process_update(req)

        page_param = {}
        self._process_read(req, page_param)

        return 'condfields_admin.html', {'template': page_param}

    def _process_read(self, req, page_param):
        ticket_type = req.args.get('type')

        ticket_types = [{
            'name': type.name,
            'value': type.value,
            'selected': type.name == ticket_type,
            'hidden': ','.join(set(self.config.getlist('condfields',
                                                       type.name + '_fields')))
        } for type in ticket.Type.select(self.env)]

        page_param['types'] = ticket_types
        standard_fields = []
        custom_fields = []
        for f in TicketSystem(self.env).get_ticket_fields():
            if f.get('custom'):
                custom_fields.append(f)
            else:
                standard_fields.append(f)
        forced_fields = self.config.getlist('condfields', 'forced_fields')
        custom_fields = [f for f in custom_fields
                           if f['name'] not in forced_fields]
        standard_fields = [f for f in standard_fields
                             if f['name'] not in forced_fields]
        page_param['customfields'] = custom_fields
        page_param['standardfields'] = standard_fields
        page_param['forcedfields'] = forced_fields

    def _process_update(self, req):
        ticket_type = req.args.get('type')
        ticket_hide = req.args.get('cf-hide')

        ticket_hide_fields = ''
        if ticket_hide is not None:
            if isinstance(ticket_hide, list):
                ticket_hide_fields = ','.join(ticket_hide)
            else:
                ticket_hide_fields = ticket_hide

        # set the configuration now
        self.config.set('condfields', ticket_type, ticket_hide_fields)
        self.config.save()
