# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.core import START, END, QName
from genshi.builder import tag
from genshi.filters.transform import StreamBuffer

from trac.core import Component, implements
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.util.translation import N_
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet

from tracticketfieldslayout.api import ListOption, get_groups


__all__ = ['TicketFieldsLayoutModule']


def _templates_default():
    from trac import __version__
    if map(int, __version__.split('.')[:2]) >= [1, 0]:
        names = ('ticket.html', 'ticket_box.html', 'ticket_preview.html')
    else:
        names = ('ticket.html',)
    return ', '.join(names)


class TicketFieldsLayoutModule(Component):

    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

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
        'ticketfieldslayout', 'templates', _templates_default(),
        doc=N_("""\
List of template names to apply the fields layout in ticket page and
ticket form"""))

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req and data and template in self._templates:
            for path in self._stylesheet_files:
                add_stylesheet(req, path)
            add_script(req, 'common/js/folding.js')
            add_script(req, 'ticketfieldslayout/web_ui.js')
        return template, data, content_type

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        path = resource_filename(__name__, 'htdocs')
        return [('ticketfieldslayout', path)]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def filter_stream(self, req, method, filename, stream, data):
        if not (filename and data and 'ticket' in data and
                filename in self._templates and self._fields):
            return stream
        fields = [f.lower() for f in self._fields if f]
        if fields == self._default_fields():
            return stream
        groups = get_groups(self.config)
        self._prepend_stdprops(fields, groups)
        stream |= TicketFieldsLayoutTransformer(fields, groups, req, data)
        return stream

    def _default_fields(self):
        protected_fields = set(Ticket.protected_fields)
        names = [f['name'] for f in TicketSystem(self.env).get_ticket_fields()]
        return [name for name in names if name not in protected_fields]

    def _prepend_stdprops(self, fields, groups):
        used = set(fields)
        for group in groups.itervalues():
            used.update(group['fields'])
        fields[0:0] = (name for name in ('summary', 'reporter', 'owner',
                                         'description')
                            if name not in used)


class TicketFieldsLayoutTransformer(object):

    def __init__(self, fields, groups, req, data):
        self.fields = fields
        self.groups = groups
        self.data = data
        self.ticket = data['ticket']
        self.preview_form = bool(req.args.getfirst('preview'))
        self.preview_ajax = bool(data.get('preview_mode'))  # since Trac 1.0
        names = [f['name'] for f in self.ticket.fields]
        self.ticket_fields = dict((name, self.ticket[name])
                                  for name in names
                                  if name not in self.ticket.protected_fields)

    def __call__(self, stream):
        transformed_form = transformed_ticket_box = False

        for event in stream:
            kind, data, pos = event
            if kind is not START:
                yield event
                continue
            localname = data[0].localname
            if (transformed_form is False and localname == 'fieldset' and
                data[1].get('id') == 'properties'):
                yield event
                for event in self.transform_form(stream):
                    yield event
                transformed_form = True
                if transformed_ticket_box is True:
                    break
                continue
            if (transformed_ticket_box is False and localname == 'div' and
                data[1].get('id') == 'ticket'):
                yield event
                for event in self.transform_ticket_box(stream):
                    yield event
                transformed_ticket_box = True
                if transformed_form is True:
                    break
                continue
            yield event

        for event in stream:
            yield event

    def transform_form(self, stream):
        depth = 1
        table_depth = depth
        for event in stream:
            kind, data, pos = event
            if kind is START:
                depth += 1
                if data[0].localname == 'table':
                    table_depth = depth
                    yield event
                    break
            elif kind is END:
                depth -= 1
            yield event
            if depth == 0:
                return

        field_name = None
        fullrow = None
        cells = {}
        cell_buf = None
        cell_depth = None
        last_event = None
        for event in stream:
            kind, data, pos = event
            if kind is END:
                depth -= 1
                if depth < table_depth:
                    last_event = event  # END of <table>
                    break
            if kind is not START:
                continue

            depth += 1
            localname = data[0].localname
            if localname == 'th':
                cell_depth = depth - 1
                cell_buf = StreamBuffer()
                cell_buf.append(event)
                for event in stream:
                    cell_buf.append(event)
                    kind, data, pos = event
                    if kind is START:
                        depth += 1
                    elif kind is END:
                        depth -= 1
                        if cell_depth == depth:
                            break
                continue

            if localname == 'td':
                cell_depth = depth - 1
                fullrow = data[1].get('colspan') == '3'
                if cell_buf is None:
                    cell_buf = StreamBuffer()
                cell_buf.append(event)
                for event in stream:
                    cell_buf.append(event)
                    kind, data, pos = event
                    if kind is START:
                        depth += 1
                        if field_name is None and \
                                data[0].localname in ('input', 'select',
                                                      'textarea'):
                            tmp = data[1].get('name', '')
                            if tmp.startswith('field_'):
                                field_name = tmp[6:]
                    elif kind is END:
                        depth -= 1
                        if cell_depth == depth:
                            break
                if field_name is not None and cell_buf is not None:
                    cells[field_name] = {'fullrow': fullrow,
                                         'buffer': cell_buf}
                cell_buf = field_name = None

        def list_except_owner(names):
            return [name for name in names if name != 'owner']

        def iter_cell(cell):
            idx = cell_idx[0]
            if cell['fullrow'] and idx % 2 == 1:
                yield tr_end
                idx = 0
            if idx % 2 == 0:
                yield tr_start
            for event in cell['buffer']:
                kind, data, pos = event
                if kind is START and data[0].localname in ('th', 'td'):
                    col = 'col%d' % (idx % 2 + 1)
                    attrs = data[1]
                    class_ = attrs.get('class') or ''
                    if col not in class_:
                        class_ = set(class_.split())
                        class_.discard('col%d' % ((idx + 1) % 2 + 1))
                        class_.add(col)
                        attrs |= [(qname_class, ' '.join(class_))]
                    data = (data[0], attrs)
                yield kind, data, pos
            if idx % 2 == 1:
                yield tr_end
            if cell['fullrow']:
                idx = 0
            else:
                idx += 1
            cell_idx[0] = idx

        def iter_fields(fields):
            fields = [name for name in fields
                           if name and name not in used_fields]
            for name in fields:
                if name in used_fields:
                    continue
                used_fields.add(name)
                if not name.startswith('@'):
                    if name not in self.ticket_fields or name not in cells:
                        continue
                    for event in iter_cell(cells[name]):
                        yield event
                    continue
                group = self.groups.get(name[1:])
                if not group:
                    continue
                group_fields = list_except_owner(group['fields'])
                if not group_fields:
                    continue
                if cell_idx[0] % 2 == 1:
                    yield tr_end
                yield tr_start
                fragment = iter(self.create_group(group, ticket_box=False))
                for event in fragment:
                    yield event
                    kind, data, pos = event
                    if kind is START and data[0].localname == 'table':
                        break
                for event in self.create_colgroup():
                    yield event
                cell_idx[0] = 0
                for event in iter_fields(group_fields):
                    yield event
                for event in fragment:
                    yield event
                cell_idx[0] = 0
            if cell_idx[0] % 2 == 1:
                for event in tag(tag.th(class_='col2'), tag.td(class_='col2')):
                    yield event
                yield tr_end

        qname_class = QName('class')
        tr_start, tr_end = list(tag.tr)
        used_fields = set()
        cell_idx = [0]
        for event in self.create_colgroup():
            yield event
        fields = list_except_owner(self.fields)
        fields.append('owner')
        for event in iter_fields(fields):
            yield event
        yield last_event  # END of <table>

        if not self.ticket.exists:
            hiddens = tag.div
            for name, value in self.ticket_fields.iteritems():
                if name in used_fields:
                    continue
                hiddens.append(tag.input(type='hidden', name=name,
                                         value=value))
            for event in hiddens:
                yield event

    def transform_ticket_box(self, stream):
        depth = 1
        table_depth = depth
        for event in stream:
            kind, data, pos = event
            if kind is START:
                depth += 1
                if (data[0].localname == 'table' and
                    data[1].get('class') == 'properties'):
                    table_depth = depth
                    yield event
                    break
            elif kind is END:
                depth -= 1
            yield event
            if depth == 0:
                return

        name = None
        fullrow = None
        cells = {}
        cell_buf = None
        cell_depth = None
        last_event = None

        for event in stream:
            if cell_buf is not None:
                cell_buf.append(event)
            kind, data, pos = event
            if kind is START:
                localname = data[0].localname
                tmp = None
                if localname in ('th', 'td'):
                    cell_depth = depth
                    cell_buf = StreamBuffer()
                    cell_buf.append(event)
                    fullrow = False
                    if localname == 'td':
                        fullrow = data[1].get('colspan') == '3'
                    if localname == 'th':
                        tmp = data[1].get('id')
                    else:
                        tmp = data[1].get('headers')
                    if tmp and tmp.startswith('h_'):
                        name = tmp[2:]
                elif cell_buf is None or name:
                    pass
                depth += 1
                continue

            if kind is not END:
                continue

            depth -= 1
            if depth == cell_depth:
                if name and cell_buf is not None:
                    if name not in cells:
                        cells[name] = {'fullrow': None, 'buffer': None}
                    cell = cells[name]
                    if fullrow is not None:
                        cell['fullrow'] = fullrow
                    buf = cell['buffer']
                    if buf:
                        for event in cell_buf:
                            buf.append(event)
                    else:
                        cell['buffer'] = cell_buf
                cell_buf = name = None
            if depth < table_depth:
                last_event = event  # END of <table>
                break

        def iter_cell(cell):
            idx = cell_idx[0]
            if cell['fullrow'] and idx % 2 == 1:
                yield tr_end
                idx = 0
            if idx % 2 == 0:
                yield tr_start
            for event in cell['buffer']:
                yield event
            if idx % 2 == 1:
                yield tr_end
            if cell['fullrow']:
                idx = 0
            else:
                idx += 1
            cell_idx[0] = idx

        def iter_fields(fields):
            fields = [name for name in fields
                           if name and name not in used_fields]
            for name in fields:
                if name in used_fields:
                    continue
                used_fields.add(name)
                if not name.startswith('@'):
                    if name not in self.ticket_fields or name not in cells:
                        continue
                    for event in iter_cell(cells[name]):
                        yield event
                    continue
                group = self.groups.get(name[1:])
                if not group or not group['fields']:
                    continue
                if cell_idx[0] % 2 == 1:
                    yield tr_end
                yield tr_start
                fragment = iter(self.create_group(group, ticket_box=True))
                for event in fragment:
                    yield event
                    kind, data, pos = event
                    if kind is START and data[0].localname == 'table':
                        break
                for event in self.create_colgroup():
                    yield event
                cell_idx[0] = 0
                for event in iter_fields(group['fields']):
                    yield event
                for event in fragment:
                    yield event
                cell_idx[0] = 0
            if cell_idx[0] % 2 == 1:
                yield tr_end

        tr_start, tr_end = list(tag.tr)
        used_fields = set()
        cell_idx = [0]
        for event in self.create_colgroup():
            yield event
        for event in iter_fields(self.fields):
            yield event
        yield last_event  # END of <table>

    def create_group(self, group, ticket_box=None):
        anchor = tag.a(group['label'], href='javascript:void(0)',
                       onclick="jQuery(this).parent().parent()"
                               ".toggleClass('collapsed')")
        legend = tag.legend(anchor,
                            class_=('ticketfieldslayout-foldable',
                                    'foldable')[bool(self.preview_ajax)])
        table = tag.table(class_=(None, 'properties')[ticket_box])
        collapsed = (None, 'collapsed')[
                group['collapsed'] and
                (not ticket_box or not self.preview_form and
                                   not self.preview_ajax)]
        return tag.td(tag.fieldset(legend, table, class_=collapsed),
                      colspan='4')

    def create_colgroup(self):
        fragment = tag.colgroup
        for value in ('ticketfieldslayout-col-th',
                      'ticketfieldslayout-col-td',
                      'ticketfieldslayout-col-th',
                      'ticketfieldslayout-col-td'):
            fragment(tag.col(class_=value))
        return fragment
