# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2023 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import itertools
import pkg_resources

from trac import __version__
from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.util import lazy
from trac.util.translation import N_
from trac.web.api import IRequestFilter
from trac.web.chrome import (ITemplateProvider, add_script, add_script_data,
                             add_stylesheet)

from .api import (
    ListOption, get_default_fields, use_jinja2, get_groups, iteritems,
    itervalues,
)


__all__ = ('TicketFieldsLayoutModule',)


_interfaces = [IRequestFilter, ITemplateProvider]

if use_jinja2:
    ITemplateStreamFilter = TicketFieldsLayoutTransformer = None
else:
    from trac.web.api import ITemplateStreamFilter
    from ._genshi import TicketFieldsLayoutTransformer
    _interfaces.append(ITemplateStreamFilter)

_htdocs_dir = pkg_resources.resource_filename(__name__, 'htdocs')
_templates_dir = pkg_resources.resource_filename(__name__,
                    'templates/%s' % ('jinja2' if use_jinja2 else 'genshi'))


if use_jinja2:
    _templates_default = 'ticket.html,ticket_preview.html,ticket_box.html'
elif not __version__.startswith('0.'):
    _templates_default = 'ticket.html,ticket_box.html,ticket_preview.html'
else:
    _templates_default = 'ticket.html'


class TicketFieldsLayoutModule(Component):

    implements(*_interfaces)

    _fields = ListOption(
        'ticketfieldslayout', 'fields', '', doc=N_("""\
List of comma delimited field names of ticket and group names which
start with an `@` character. A group defines as `group.<name>` in the
section.

{{{
[ticketfieldslayout]
fields = summary,reporter,owner,description,@stdprop
group.stdprop = type,priority,milestone,component,cc
group.stdprop.label = Standard properties
group.stdprop.collapsed = enabled
group.unused = keywords
}}}"""))

    _stylesheet_files = ListOption(
        'ticketfieldslayout', 'stylesheet_files',
        'ticketfieldslayout/web_ui.css',
        doc=N_("""\
File names of the stylesheet which the plugin adds to ticket page and
ticket form"""))

    _templates = ListOption(
        'ticketfieldslayout', 'templates', _templates_default,
        doc=N_("""\
List of template names to apply the fields layout in ticket page and
ticket form"""))

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req and data and template:
            fields, groups = self._fields_and_groups
            if template in self._templates:
                for path in self._stylesheet_files:
                    add_stylesheet(req, path)
                add_script(req, 'ticketfieldslayout/web_ui.js')
                if fields:
                    data.update(self._create_template_data(
                                            data['fields'], fields, groups))
            if 'common/js/query.js' in (req.chrome.get('scriptset') or set()):
                add_script(req, 'ticketfieldslayout/query.js')
                if fields:
                    fields = list(Ticket.protected_fields) + fields
                else:
                    fields = list(Ticket.protected_fields)
                    used_fields = set(fields)
                    fields.extend(f['name']
                                  for f in TicketSystem(self.env).fields
                                  if f['name'] not in used_fields)
                fields.append('id')
                script_data = {'fields': fields, 'groups': groups or {}}
                add_script_data(req, {'ticketfieldslayout': script_data})
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        yield 'ticketfieldslayout', _htdocs_dir

    def get_templates_dirs(self):
        yield _templates_dir

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if not (filename and data and 'ticket' in data and
                filename in self._templates and self._fields):
            return stream

        fields, groups = self._fields_and_groups
        if fields:
            stream |= TicketFieldsLayoutTransformer(fields, groups, req, data)
        return stream

    if not ITemplateStreamFilter:
        del filter_stream

    # Internal methods

    def _create_template_data(self, fields_list, fields, groups):
        fields_map = dict((f['name'], f.copy()) for f in fields_list)
        if 'description' in fields_map:
            fields_map['description'].setdefault('height', 10)
        grouped_fields = []
        unnamed = 0
        groups = dict((key, group.copy()) for key, group in iteritems(groups))
        keyfunc = lambda f: f if f.startswith('@') else None
        for key, fields in itertools.groupby(fields, keyfunc):
            if key and key.startswith('@'):
                grouped_fields.append(key)
            else:
                key = '_unnamed.%d' % unnamed
                fields = list(fields)
                unnamed += 1
                grouped_fields.append(key)
                groups[key] = {'name': key, 'fields': fields}
        for group in itervalues(groups):
            group['field_items'] = [fields_map[name]
                                    for name in group['fields']]

        return {
            'ticketfieldslayout': {'fields': grouped_fields, 'groups': groups},
        }

    @lazy
    def _fields_and_groups(self):
        return self._get_fields_and_groups(get_default_fields(self.env))

    def _get_fields_and_groups(self, default_fields):
        fields = [f.lower() for f in self._fields if f]
        if fields == default_fields:
            return None, None
        else:
            groups = get_groups(self.config)
            self._prepend_stdprops(fields, groups)
            return fields, groups

    def _prepend_stdprops(self, fields, groups):
        used = set(fields)
        for group in itervalues(groups):
            used.update(group['fields'])
        fields[0:0] = (name for name in ('summary', 'reporter', 'owner',
                                         'description')
                            if name not in used)
