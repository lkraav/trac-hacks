# -*- coding: utf-8 -*-
from operator import methodcaller

from trac.core import Component, implements
from trac.ticket.model import Ticket
from trac.web.api import IRequestFilter, ITemplateStreamFilter

from genshi.builder import tag
from genshi.filters.transform import Transformer


class MultiSelectBox(Component):
    """Extend the custom ticket field as a multiple selectbox."""

    implements(IRequestFilter, ITemplateStreamFilter)

    DEFAULT_SELECT_SIZE = 4
    TICKET_PATH = ['/ticket', '/newticket', '/simpleticket']

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.method == 'POST' and \
            any(methodcaller('startswith', path)(req.path_info)
                for path in self.TICKET_PATH):

            ticket_id = req.args.get('id')
            for field in self._get_multi_select_fields():
                key = 'field_%s' % field.encode('utf-8')
                values = req.args.get(key)
                if values is None and ticket_id is not None:
                    ticket = Ticket(self.env, ticket_id)
                    current_value = ticket.values.get(field)
                    if current_value != '' and current_value is not None:
                        req.args[key] = values
                elif isinstance(values, list):
                    req.args[key] = ' '.join(values)

        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            ticket = data.get('ticket', None)
            for field in self._get_multi_select_fields():
                self.set_data_for_view(req, data, ticket, field)
                stream = self.get_stream_for_edit(stream, ticket, field)

        return stream

    def set_data_for_view(self, req, data, ticket, field):
        query_format = self.config.get('query', 'ticketlink_query') + '&%s=~%s'
        base_url = req.href.query()
        for f in data['fields']:
            if f['name'] == field:
                queries = []
                for value in self._get_field_values(ticket, field):
                    query_param = query_format % (field, value)
                    attr = {
                        'href': '%s%s' % (base_url, query_param),
                        'title': value,
                    }
                    queries.append(tag.a(value, **attr))
                    queries.append(tag.br())

                if queries:
                    # set own tag for pretty print
                    f['rendered'] = tag(queries)

    def get_stream_for_edit(self, stream, ticket, field):
        xpath = '//input[@id="field-%s"]' % field
        attr = {
            'id': 'field-%s' % field,
            'name': 'field_%s' % field,
            'size': self._get_select_size(field),
            'multiple': 'multiple',
        }
        # update stream from input tag to multi select
        return stream | Transformer(xpath).replace(
            tag.select(**attr)(self._get_select_options(field, ticket)))

    def _get_field_values(self, ticket, field):
        values = ticket.values.get(field, None)
        return [] if values is None else values.replace(',', ' ').split()

    def _get_multi_select_fields(self):
        conf = self.config['ticket-custom']
        for key, value in conf.options():
            if key.endswith('.multiple') and conf.getbool(key):
                yield key.split('.', 1)[0]

    def _get_select_options(self, field, ticket=None):
        selected = None
        if ticket is not None:
            selected = self._get_field_values(ticket, field)

        key = '%s.options' % field
        conf_options = self.config.getlist('ticket-custom', key, sep=' ')
        options = tag()
        for opt in conf_options:
            tag_option = tag.option(opt)
            if selected and opt in selected:
                tag_option(selected='selected')
            options(tag_option)
        return options

    def _get_select_size(self, field):
        key = '%s.size' % field
        return self.config.get('ticket-custom', key, self.DEFAULT_SELECT_SIZE)
