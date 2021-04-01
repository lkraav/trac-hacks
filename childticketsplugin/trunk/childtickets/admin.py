# -*- coding: utf-8 -*-
#
# Copyright (C) Mark Ryan
# Copyright (C) Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
from pkg_resources import get_distribution, parse_version
from trac.admin import IAdminPanelProvider
from trac.core import *
from trac.ticket.api import TicketSystem
from trac.ticket.model import Type
from trac.util.text import exception_to_unicode
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider
from trac.web.chrome import add_notice, add_warning, add_stylesheet


# Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
# creation using trac.util.html.tag and friends
pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')

def _save_config(config, req, log):
    """Try to save the config, and display either a success notice or a
    failure warning.
    """
    try:
        config.save()
        add_notice(req, _('Your changes have been saved.'))
    except Exception as e:
        log.error('Error writing to trac.ini: %s', exception_to_unicode(e))
        add_warning(req, _('Error writing to trac.ini, make sure it is '
                           'writable by the web server. Your changes have not '
                           'been saved.'))


class ChildTicketsAdminPanel(Component):
    """Configure which ticket types allow children, inherited fields for children and more.

    All the settings may be controlled from the admin pages. They are saved
    in ''trac.ini'' as shown below.

    The following global settings are available:
    [[TracIni(childtickets)]]

    You may specify features for each ticket type. In this example the configuration
    is for tickets of type {{{defect}}}:
    {{{#!ini
    [childtickets]
    parent.defect.allow_child_tickets = True
    parent.defect.inherit = description,milestone,summary,project,version
    parent.defect.restrict_child_type = defect,enhancement
    parent.defect.table_headers = status,project,summary
    }}}
     parent.<type>.allow_child_tickets = True|False:: if child tickets are allowed for this parent ticket type
     parent.<type>.inherit = fieldname 1, fieldname 2, ...:: specify the ticket fields which should be copied to the child
     parent.<type>.restrict_child_type = type 1, type 2, ...:: allow these types ase new child ticket types
     parent.<type>.table_headers = fieldname 1, fieldname 2, ...:: the table headers to be shown for child tickets
    """

    implements(IAdminPanelProvider, ITemplateProvider)

    def ticket_custom_field_exists(self):
        """Check if the ticket custom field 'parentt' is configured.

        :returns None if not configured, otherwise the field type

        We don't check for proper custom field type here.
        """
        return self.config.get('ticket-custom', 'parent', None)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm('admin', 'childticketsplugin/types'):
            yield ('childticketsplugin', _('Child Tickets'), 'types',
                   _('Parent Types'))
        if 'TICKET_ADMIN' in req.perm('admin', 'childticketsplugin/basics'):
            excl_mark = '' if self.ticket_custom_field_exists() else ' (!)'
            yield ('childticketsplugin', _('Child Tickets'), 'basics',
                   _('Basic Settings') + excl_mark)

    def _render_admin_basics(self, req, cat, page, parenttype):
        # Only for trac admins.
        req.perm('admin', 'childticketsplugin/basics').require('TICKET_ADMIN')

        data = {
            'custom_field': self.ticket_custom_field_exists(),
            'custom_field_label': _('Parent'),
            'max_view_depth_val': self.config.getint('childtickets', 'max_view_depth', default=3),
            'recursion_warn': self.config.getint('childtickets', 'recursion_warn', default=7)
        }

        if req.method == 'POST':
            if req.args.get('create-ticket-custom'):
                self.config.set('ticket-custom', 'parent', 'text')
                self.config.set('ticket-custom', 'parent.label', req.args.get('custom-field-label-val', _('Parent')))
                self.config.set('ticket-custom', 'parent.format', 'wiki')
                self.config.save()
                add_notice(req, _("The ticket custom field 'parent' was added to the configuration."))
            elif req.args.get('max-view-depth'):
                self.config.set('childtickets', 'max_view_depth', req.args.get('max-view-depth-val', 3))
                self.config.save()
                add_notice(req, _('Your changes have been saved.'))
            elif req.args.get('recursion-warn'):
                self.config.set('childtickets', 'recursion_warn', req.args.get('recursion-warn-val', 7))
                self.config.save()
                add_notice(req, _('Your changes have been saved.'))

            req.redirect(req.href.admin(cat, page))

        if pre_1_3:
            return 'admin_ct_basics.html', data
        else:
            return 'admin_ct_basics_jinja.html', data

    def render_admin_panel(self, req, cat, page, parenttype):

        if page == 'basics':
            return self._render_admin_basics(req, cat, page, parenttype)

        # Only for trac admins.
        req.perm('admin', 'childticketsplugin/types').require('TICKET_ADMIN')

        if req.method == 'POST':
            if req.args.get('create-ticket-custom'):
                self.config.set('ticket-custom', 'parent', 'text')
                self.config.set('ticket-custom', 'parent.label', req.args.get('custom-field-label-val', _('Parent')))
                self.config.set('ticket-custom', 'parent.format', 'wiki')
                self.config.save()
                add_notice(req, _("The ticket custom field 'parent' was added to the configuration."))
                req.redirect(req.href.admin(cat, page))

        # Detail view?
        if parenttype:
            if req.method == 'POST':
                allow_child_tickets = \
                    req.args.get('allow_child_tickets')
                self.config.set('childtickets',
                                'parent.%s.allow_child_tickets'
                                % parenttype,
                                allow_child_tickets)

                headers = req.args.getlist('headers')
                self.config.set('childtickets',
                                'parent.%s.table_headers' % parenttype,
                                ','.join(headers))

                restricted = req.args.getlist('restricted')
                self.config.set('childtickets',
                                'parent.%s.restrict_child_type' % parenttype,
                                ','.join(restricted))

                inherited = req.args.getlist('inherited')
                self.config.set('childtickets',
                                'parent.%s.inherit' % parenttype,
                                ','.join(inherited))

                _save_config(self.config, req, self.log),
                req.redirect(req.href.admin(cat, page))

            # Convert to object.
            parenttype = ParentType(self.config, parenttype)

            data = {
                'view': 'detail',
                'parenttype': parenttype,
                'table_headers': self._headers(parenttype),
                'parent_types': self._types(parenttype),
                'inherited_fields': self._inherited(parenttype),
                'field_names': TicketSystem(self.env).get_ticket_field_labels()
            }
        else:
            data = {
                'custom_field': self.ticket_custom_field_exists(),
                'custom_field_label': _('Parent'),
                'view': 'list',
                'base_href': req.href.admin(cat, page),
                'ticket_types': [ParentType(self.config, p) for p in self.ticket_types],
                'field_names': TicketSystem(self.env).get_ticket_field_labels()
            }

        # Add our own styles for the ticket lists.
        add_stylesheet(req, 'ct/css/childtickets.css')

        if pre_1_3:
            return 'admin_childtickets.html', data
        else:
            return 'admin_childtickets_jinja.html', data

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ct', resource_filename(__name__, 'htdocs'))]

    # Custom methods
    def _headers(self, ptype):
        """Returns a list of valid headers for the given parent type.
        """
        ticket_fields = [item['name'] for item in TicketSystem(self.env).get_ticket_fields()]
        # Description is always shown so don't allow user to select/deselect it
        headers = [item for item in ticket_fields if item != 'description']
        headers = dict.fromkeys(headers, None)
        headers.update(
            dict.fromkeys(map(lambda x: x.lower(), ptype.table_headers),
                          'checked'))
        return headers

    def _inherited(self, ptype):
        """Returns a list of inherited fields.
        """
        ticket_fields = [item['name'] for item in TicketSystem(self.env).get_ticket_fields()]
        inherited = dict.fromkeys(ticket_fields, None)
        inherited.update(
            dict.fromkeys(map(lambda x: x.lower(), ptype.inherited_fields),
                          'checked'))
        return inherited

    @property
    def ticket_types(self):
        return [item.name for item in Type.select(self.env)]

    def _types(self, ptype):
        """
        Return a dictionary with info as to whether the parent type
        is already selected as an available child type.
        """
        types = dict.fromkeys(x for x in self.ticket_types)
        types.update(dict.fromkeys(
            map(lambda x: x.lower(), ptype.restrict_to_child_types),
            'checked'))
        return types


class ParentType(object):
    def __init__(self, config, name):
        self.name = name
        self.config = config

    @property
    def allow_child_tickets(self):
        return self.config.getbool('childtickets',
                                   'parent.%s.allow_child_tickets' % self.name,
                                   default=False)

    @property
    def table_headers(self):
        return self.config.getlist('childtickets',
                                   'parent.%s.table_headers' % self.name,
                                   default=['summary', 'owner'])

    @property
    def restrict_to_child_types(self):
        return self.config.getlist('childtickets',
                                   'parent.%s.restrict_child_type' % self.name,
                                   default=[])

    @property
    def inherited_fields(self):
        return self.config.getlist('childtickets',
                                   'parent.%s.inherit' % self.name,
                                   default=[])

    @property
    def default_child_type(self):
        return self.config.get('childtickets',
                               'parent.%s.default_child_type' % self.name,
                               default=self.config.get('ticket',
                                                       'default_type'))

    @property
    def table_row_class(self):
        """Return a class (enabled/disabled) for the table row - allows it
        to 'look' disabled if not active.
        """
        if self.allow_child_tickets:
            return 'enabled'
        return 'disabled'
