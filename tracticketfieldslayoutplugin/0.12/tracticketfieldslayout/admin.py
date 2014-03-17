# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.admin.api import IAdminPanelProvider
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.util import hex_entropy
from trac.util.translation import dgettext
from trac.web.chrome import Chrome, add_notice, add_script, add_stylesheet

from tracticketfieldslayout.api import get_groups, _
from tracticketfieldslayout.web_ui import TicketFieldsLayoutModule


__all__ = ['TicketFieldsLayoutAdminModule']


_SECTION = 'ticketfieldslayout'


class TicketFieldsLayoutAdminModule(Component):

    implements(IAdminPanelProvider)

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            return [('ticket', (dgettext)('messages', "Ticket System"),
                     'ticketlayout', _("Ticket Layout"))]

    def render_admin_panel(self, req, category, page, path_info):
        req.perm.require('TICKET_ADMIN')
        add_stylesheet(req, 'ticketfieldslayout/admin.css')
        if hasattr(Chrome, 'add_jquery_ui'):
            Chrome(self.env).add_jquery_ui(req)
        else:
            add_script(req, 'ticketfieldslayout/jquery-ui.js')
        add_script(req, 'ticketfieldslayout/admin.js')

        if req.method == 'POST':
            func = None
            if req.args.getfirst('apply'):
                func = self._process_field_apply
            elif req.args.getfirst('restore'):
                func = self._process_field_restore
            if func is None:
                req.redirect(req.href('admin', category, page))
            func(req, category, page, path_info)

        return self._process_view(req, category, page, path_info)

    def _process_view(self, req, category, page, path_info):
        mod = TicketFieldsLayoutModule(self.env)
        ticket_fields = [f for f in TicketSystem(self.env).get_ticket_fields()
                           if f['name'] not in Ticket.protected_fields]
        ticket_fields_map = dict((f['name'], f) for f in ticket_fields)
        ticket_field_names = [f['name'] for f in ticket_fields]
        groups_map = get_groups(self.config)
        used_fields = set()

        root_fields = []
        groups = []
        for name in (mod._fields or ticket_field_names):
            if not name:
                continue
            name = name.lower()
            if name in used_fields:
                continue
            used_fields.add(name)

            if not name.startswith('@'):
                if name not in ticket_fields_map:
                    continue
                field = ticket_fields_map[name]
                root_fields.append({'group': None, 'name': name,
                                    'label': field['label']})
            else:
                group = groups_map.get(name[1:])
                if not group:
                    continue
                groups.append(group)
                root_fields.append({'group': group, 'name': name,
                                    'label': group['label']})

        for group in groups:
            fields = []
            for name in group['fields']:
                if name in used_fields or name not in ticket_fields_map:
                    continue
                used_fields.add(name)
                fields.append(ticket_fields_map[name])
            group['fields'] = fields

        hiddens = []
        for name in ticket_field_names:
            if name in used_fields:
                continue
            hiddens.append({'name': name,
                            'label': ticket_fields_map[name]['label']})

        data = {'groups': groups, 'fields': root_fields, 'hiddens': hiddens}
        return 'ticketfieldslayout_admin.html', data

    def _process_field_apply(self, req, category, page, path_info):
        tktsys = TicketSystem(self.env)
        custom_fields_count = len(tktsys.custom_fields)
        custom_fields = dict((field['name'], idx + custom_fields_count)
                             for idx, field
                             in enumerate(tktsys.custom_fields))

        options = {'fields': req.args.getlist('field')}
        group_names = [name[1:] for name in options['fields']
                                if name.startswith('@')]

        for name in group_names:
            if '=' in name:
                continue
            prefix = 'group.' + name
            options[prefix] = [
                    val for val in req.args.getlist('field.' + name)
                        if not val.startswith('@')]
            options[prefix + '.label'] = req.args.getfirst('label.' + name, '')
            collapsed = bool(req.args.getfirst('collapsed.' + name))
            options[prefix + '.collapsed'] = ('disabled', 'enabled')[collapsed]

        def iter_fields(key):
            for name in options.get(key, ()):
                if not name.startswith('@'):
                    yield name
                    continue
                for name in iter_fields(key='group.' + name[1:]):
                    yield name

        custom_fields_count = 0
        for name in iter_fields('fields'):
            if name in custom_fields:
                custom_fields[name] = custom_fields_count
                custom_fields_count += 1

        for name, value in self.config.options(_SECTION):
            if name.startswith('group.'):
                self.config.remove(_SECTION, name)
        for name, value in options.iteritems():
            if isinstance(value, list):
                value = ','.join(value)
            self.config.set(_SECTION, name, value)
        for idx, (name, _) in enumerate(sorted(custom_fields.iteritems(),
                                               key=lambda (k, v): v)):
            self.config.set('ticket-custom', name + '.order', idx + 1)
        self.config.save()

        self._add_notice_saved(req)
        req.redirect(req.href('admin', category, page))

    def _process_field_restore(self, req, category, page, path_info):
        self.config.remove(_SECTION, 'fields')
        self.config.save()

        add_notice(req, _("The default settings have been restored."))
        req.redirect(req.href('admin', category, page))

    def _add_notice_saved(self, req):
        add_notice(req, (dgettext)('messages',
                                   "Your changes have been saved."))

    def _new_group_name(self):
        return hex_entropy(16)
