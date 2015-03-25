# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.config import BoolOption, ListOption
from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.ticket.model import Type
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_script_data


class CondFieldsModule(Component):
    """A filter to implement conditional fields on the ticket page."""

    implements(IRequestFilter, ITemplateProvider)

    include_std = BoolOption('condfields', 'include_standard', default='true',
                             doc="Include the standard fields for all types.")

    show_default = BoolOption('condfields', 'show_default', default='false',
                              doc="Default is to show or hide selected fields.")

    forced_fields = ListOption('condfields', 'forced_fields', doc='Fields that cannot be disabled',
                               default="type, summary, reporter, description, status, resolution, priority")

    def __init__(self):
        # Initialize ListOption()s for each type.
        # This makes sure they are visible in IniAdmin, etc
        self.types = [t.name for t in Type.select(self.env)]
        for t in self.types:
            hidden_fields = ListOption('condfields', t,
                                       doc='Fields to hide for type "%s"' % t)
            setattr(self.__class__, '%s_fields' % t, hidden_fields)

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/newticket') or \
                req.path_info.startswith('/ticket/'):
            add_script_data(req, self._get_script_data(req))
            add_script(req, '/chrome/condfields/condfields.js')
        return template, data, content_type

    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('condfields', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    ### Private methods

    def _get_script_data(self, req):
        ticket_types = {}
        field_types = {}
        all_fields = []
        standard_fields = set()
        for f in TicketSystem(self.env).get_ticket_fields():
            all_fields.append(f['name'])
            field_types[f['name']] = f['type']
            if not f.get('custom'):
                standard_fields.add(f['name'])

        if 'owner' in all_fields:
            curr_idx = all_fields.index('owner')
            if 'cc' in all_fields:
                insert_idx = all_fields.index('cc')
            else:
                insert_idx = len(all_fields)
            if curr_idx < insert_idx:
                all_fields.insert(insert_idx, all_fields[curr_idx])
                del all_fields[curr_idx]

        for t in self.types:
            if not self.show_default:
                hiddenfields = set(getattr(self, t + '_fields'))
                fields = set(all_fields)
                fields.difference_update(hiddenfields)
            else:
                fields = set(getattr(self, t+'_fields'))
                if self.include_std:
                    fields.update(standard_fields)
            fields.update(set(self.forced_fields))
            ticket_types[t] = dict([
                (f, f in fields) for f in all_fields
            ])

        return {
            'mode': 'new' if req.path_info.startswith('/newticket')
                          else 'view',
            'condfields': ticket_types,
            'field_types': field_types,
            'required_fields': list(self.forced_fields)
        }
