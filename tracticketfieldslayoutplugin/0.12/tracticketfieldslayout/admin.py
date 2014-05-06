# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.admin.api import IAdminPanelProvider
from trac.admin.web_ui import AdminModule
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.util.translation import gettext as _gettext
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome, add_notice, add_script, add_stylesheet

from tracticketfieldslayout.api import get_default_fields, get_groups, _
from tracticketfieldslayout.web_ui import TicketFieldsLayoutModule


__all__ = ['TicketFieldsLayoutAdminModule']


_SECTION = 'ticketfieldslayout'


class TicketFieldsLayoutAdminModule(Component):

    implements(IAdminPanelProvider, IRequestFilter)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', _gettext("Ticket System"),
                   'ticketlayout', _("Ticket Layout"))

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

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if req.method == 'POST' and \
                isinstance(handler, AdminModule) and \
                req.args.get('cat_id') == 'ticket' and \
                req.args.get('panel_id') == 'customfields':
            req._ticket_custom_fields = self._get_custom_fields()
            req.add_redirect_listener(self._redirected)
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # internal methods

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
        if options['fields'] == get_default_fields(self.env):
            self._clear_layout_settings()
            self.config.save()
            self._add_notice_saved(req)
            req.redirect(req.href('admin', category, page))

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
        self._clear_layout_settings()
        self.config.save()

        add_notice(req, _("The default settings have been restored."))
        req.redirect(req.href('admin', category, page))

    def _add_notice_saved(self, req):
        add_notice(req, _gettext("Your changes have been saved."))

    def _clear_layout_settings(self):
        names = ['fields']
        names.extend(name for name, value in self.config.options(_SECTION)
                          if name.startswith('group.'))
        for name in names:
            self.config.remove(_SECTION, name)

    def _redirected(self, req, url, permanent):
        old_fields = req._ticket_custom_fields
        new_fields = self._get_custom_fields()
        if new_fields == old_fields:
            return
        old_fields = set(old_fields)
        removed = old_fields - set(new_fields)
        added = [name for name in new_fields if name not in old_fields]
        if not removed and not added:
            return

        config = self.config
        options = map(lambda (name, _): name, config.options(_SECTION))
        if removed:
            for option in options:
                if not (option.startswith('group.') and
                        len(option.split('.')) == 2):
                    continue
                old = config.getlist(_SECTION, option)
                new = [val for val in old if val not in removed]
                if old == new:
                    continue
                if new:
                    config.set(_SECTION, option, ','.join(new))
                else:
                    config.remove(_SECTION, option)
                    for tmp in options:
                        if tmp.startswith(option + '.'):
                            config.remove(_SECTION, tmp)
                    # remove the group from "fields"
                    removed.add('@' + option[6:])
        old_fields = config.getlist(_SECTION, 'fields')
        new_fields = filter(lambda val: val not in removed, old_fields) + added
        if not new_fields:
            for option in options:
                if option == 'fields' or option.startswith('group.'):
                    config.remove(_SECTION, option)
        elif old_fields != new_fields:
            config.set(_SECTION, 'fields', ','.join(new_fields))
        config.save()

    def _get_custom_fields(self):
        return [f['name'] for f in TicketSystem(self.env).get_custom_fields()]
