# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import get_distribution, parse_version
from pkg_resources import resource_filename
from ticketfieldfilter.transformer import JTransformer
from trac.admin.api import IAdminPanelProvider
from trac.config import ListOption
from trac.core import Component, implements
from trac.perm import PermissionSystem
from trac.ticket.api import TicketSystem
from trac.ticket.model import Type
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data, add_stylesheet, ITemplateProvider

try:
    dict.iteritems
except AttributeError:
    # Python 3
    def iteritems(d):
        return iter(d.items())
else:
    # Python 2
    def iteritems(d):
        return d.iteritems()

# Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
# creation using trac.util.html.tag and friends
pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')


class TicketFieldFilter(Component):
    """Filter ticket fields depending on ticket type and user permissions.

    Configuration is done on the admin page ''Ticket Fields''. You may also configure the fields
    in the configuration file ''trac.ini''.

    === Configuration
    Note that the following fields can't be removed from the ticket page:

    {{{time, changetime, attachment}}}

    For each ticket type you may set:
    * Which fields to show at all
    * If a shown field is read only. Read only fields don't show up in the ''Modify'' section.
    * A permission for a field. If the user doesn't have the necessary permission, the field is removed.

    Note that permissions only apply to fields which are enabled at all for the ticket type.

    Each entry in ''trac.ini'' starts with the ticket type.
    {{{#!ini
    [ticket-field-filter]
    <type>.fields = component, cc, type, ...
    <type>.readonly = component, cc, ...
    <type>.permission = component: PERM_1 | TICKET_CREATE, cc: PERM_2, ...
    }}}
    Leaving the entry {{{<type>.fields}}} empty disables all fields for the ticket type. Removing the entry completely
    enables all fields. Another way is to specify ''+'':

    {{{#!ini
    [ticket-field-filter]
    # enable all fields for ticket type 'defect'
    defect.fields = +
    }}}

    If the permission entry is missing or left empty no permission check takes place.

    You may specify a list of fields which are always shown:

    [[TracIni(ticket-field-filter)]]

    Default is: {{{summary, reporter, owner, description, status}}}.
    """

    implements(IAdminPanelProvider, IRequestFilter, ITemplateProvider)

    _req_fields = ListOption('ticket-field-filter', 'required_fields',
                             ['summary', 'reporter', 'owner', 'description', 'status'],
                              doc="List of ticket fields which are required and thus always shown.")

    required_fields = None

    tkt_fields = {}

    def __init__(self):
        self.required_fields = set(self._req_fields + ['time', 'changetime', 'attachment', 'resolution'])
        self.tkt_fields, self.fields_readonly, self.field_perms = self.get_configuration_for_tkt_types()

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', _('Ticket System'), 'ticketfieldfilter', 'Ticket Fields')

    def render_admin_panel(self, req, cat, page, path_info):

        all_fields = [[k, v] for k, v in iteritems(TicketSystem(self.env).get_ticket_field_labels())
                      if k not in self.required_fields]
        # Update now, because we may have come from a POST redirect
        self.tkt_fields, self.fields_readonly, self.field_perms = self.get_configuration_for_tkt_types()

        if req.method == 'POST' and page == 'ticketfieldfilter':
            sel = req.args.getlist('sel')
            if not path_info:
                # Main field select page
                if req.args.get('save'):
                    # Save enabled fields to config
                    if len(sel) != len(all_fields):
                        self.env.config.set('ticket-field-filter', '%s.fields' % req.args.get('type'), ','.join(sel))
                    else:
                        # Allow all fields
                        self.env.config.set('ticket-field-filter', '%s.fields' % req.args.get('type'), '+')
                    # Save readonly fields to config
                    sel = req.args.getlist('readonly')
                    if len(sel) != len(all_fields):
                        self.env.config.set('ticket-field-filter', '%s.readonly' % req.args.get('type'), ','.join(sel))
                    else:
                        # Allow all fields
                        self.env.config.set('ticket-field-filter', '%s.readonly' % req.args.get('type'), '+')
                    self.env.config.save()
                    req.redirect(req.href.admin(cat, page) + '#%s_form' % req.args.get('type'))
                elif req.args.get('permissions'):
                    req.redirect(req.href.admin(cat, 'ticketfieldfilter', req.args.get('type')))
            else:
                # Handling of permissions
                if req.args.get('save'):
                    tkt_type = req.args.get('type')
                    # Set new permission for the given ticket field
                    if sel:
                        self.field_perms[tkt_type][req.args.get('field')] = sel
                    else:
                        del self.field_perms[tkt_type][req.args.get('field')]
                    # Save all permissions for current ticket type
                    self.env.config.set('ticket-field-filter', '%s.permission' % tkt_type,
                                        ','.join(['%s:%s' % (k, '|'.join(v))
                                                  for k, v in iteritems(self.field_perms[tkt_type])]))
                    self.env.config.save()
                    req.redirect(req.href.admin(cat, 'ticketfieldfilter',
                                                req.args.get('type')) + "#%s_form" % req.args.get('field'))
                else:
                    req.redirect(req.href.admin(cat, 'ticketfieldfilter'))

        if not path_info:
            # Main page
            data = {'tkt_fields': self.tkt_fields,
                    'tkt_readonly': self.fields_readonly,
                    'all_fields': sorted(all_fields, key=lambda item: item[1])}

            add_stylesheet(req, 'ticketfieldfilter/css/admin.css')
            add_script(req, 'ticketfieldfilter/js/admin_ticketfieldfilter.js')
            # return 'admin_ticketfieldfilter.html', data, None
            if pre_1_3:
                return 'admin_ticketfieldfilter.html', data
            else:
                return 'admin_ticketfieldfilter_jinja.html', data
        else:
            perm = PermissionSystem(self.env)
            data = {'tkt_type': path_info,
                    'tkt_fields': all_fields if '+' in self.tkt_fields[path_info] else self.tkt_fields,
                    'all_perms': sorted(perm.get_actions()),
                    'all_fields': sorted(all_fields, key=lambda item: item[1]),
                    'field_perms': self.field_perms[path_info]}
            add_stylesheet(req, 'ticketfieldfilter/css/admin.css')
            add_script(req, 'ticketfieldfilter/js/admin_ticketfieldpermissions.js')
            if pre_1_3:
                return 'admin_ticketfieldpermissions.html', data
            else:
                return 'admin_ticketfieldpermissions_jinja.html', data

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        """Hide ticket fields according to settings"""

        if template == 'ticket.html' and data is not None and \
                'fields' in data and \
                data['fields'] is not None:
            # Make sure we have the proper data. An admin may have created a new type in the meantime.
            self.tkt_fields, self.fields_readonly, self.field_perms = self.get_configuration_for_tkt_types()
            tkt = data.get('ticket')
            if tkt:
                filter_list = []
                try:
                    for item in self.fields_readonly[tkt['type']]:
                        self.log.info('  ### field: %s' % item)
                        if item != 'type':
                            # xpath: //label[@for="field-%s"] % item
                            xform = JTransformer('label[for=field-%s]' % item)
                            filter_list.append(xform.remove())
                            # xpath: //*[@id="field-%s"] % item
                            filter_list.append(JTransformer('#field-%s' % item).remove())
                        else:
                            # Label isn't changed  to Type (fixed):atm
                            # Need to get the translated label for this instead of hard coding it
                            #
                            # Transformer('//label[@for="field-type"]/text()').replace('Type (Fixed):')

                            # xpath: //*[@id="field-type"]/option
                            filter_list.append(JTransformer('#field-type > option').remove())
                            # xpath: //*[@id="field-type"]
                            filter_list.append(JTransformer('#field-type').append('<option>%s</option>' % tkt['type']))
                except KeyError:
                    pass  # This may happen when an admin deleted a ticket type while we preview a ticket using
                          # this type.
                js_data = {'tff_filter': filter_list}

                if self.tkt_fields:
                    js_data.update({'tff_newticket': 1 if req.path_info == '/newticket' else 0})
                    add_script(req, 'ticketfieldfilter/js/ticketfieldfilter.js')

                add_script_data(req, js_data)
                add_script(req, 'ticketfieldfilter/js/tff_jtransform.js')

                tkt_type = tkt['type']
                try:
                    if '+' not in self.tkt_fields[tkt_type]:
                        # Only show fields specified in trac.ini
                        self.log.debug("TicketFieldFilter: Filtering ticket fields for type '%s'" % tkt_type)
                        # The fields to be shown.
                        fields = set(self.tkt_fields[tkt_type]) | self.required_fields
                        perms = self.field_perms[tkt_type]
                        for field in data['fields']:
                            field['skip'] = False if field['name'] in fields and not field['skip'] else True
                            # Now apply permissions if any
                            if field['name'] in perms:
                                skip = True
                                for perm in perms[field['name']]:
                                    if perm in req.perm:
                                        skip = False
                                        break
                                if skip:
                                    field['skip'] = True
                except KeyError:
                    pass  # This may happen when an admin deleted a ticket type while we preview a ticket using
                          # this type.
        return template, data, content_type

    def get_configuration_for_tkt_types(self):
        field_info = {}
        ro_info = {}
        field_perms = {}
        all_fields = [k for k, v in iteritems(TicketSystem(self.env).get_ticket_field_labels())
                      if k not in self.required_fields]

        for enum in Type.select(self.env):
            field_info[enum.name] = self.env.config.getlist('ticket-field-filter', '%s.fields' % enum.name,
                                                            all_fields)
            if '+' in field_info[enum.name]:
                field_info[enum.name] = all_fields
            ro_info[enum.name] = self.env.config.getlist('ticket-field-filter', '%s.readonly' % enum.name, [])
            if '+' in ro_info[enum.name]:
                ro_info[enum.name] = all_fields
            try:
                field_perms[enum.name] = self.parse_permission_entry(self.env.config.getlist('ticket-field-filter',
                                                                                            '%s.permission' % enum.name,
                                                                                             []))
            except ValueError:
                field_perms[enum.name] = {}

        return field_info, ro_info, field_perms

    def parse_permission_entry(self, ini_entry):
        """Create a dict from a list of key-value strings.

        @param ini_entry: list of key-value pairs describing permissions for a field.
        @return: dict with key: field name, val: list of permissions

        Each list item is a string: '<field>: PERM_1 | PERM_2 | ...' or '<field>: PERM_1'
        """
        perms = {}
        for item in ini_entry:
            k, v = item.split(':')
            perms[k] = v.replace(' ', '').split('|')
        return perms

    ## ITemplateProvider

    def get_htdocs_dirs(self):
        return [('ticketfieldfilter', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]
