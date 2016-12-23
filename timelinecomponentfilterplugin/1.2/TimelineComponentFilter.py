# -*- coding: utf-8 -*-
#

from genshi.filters import Transformer
from trac.core import *
from trac.util.html import html
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.ticket.model import Ticket


class TimelineComponentFilterPlugin(Component):
    """Filters ticket timeline events by component(s).
    """

    implements(IRequestFilter, ITemplateStreamFilter)

    ticket_types = ('newticket', 'editedticket', 'closedticket',
                    'attachment', 'reopenedticket')

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'timeline.html':
            components = req.args.getlist('filter-components')
            if components:
                filtered_events = []
                for event in data['events']:
                    if event['kind'] in self.ticket_types:
                        resource = event['kind'] == 'attachment' and \
                                   event['data'][0].parent or \
                                   event['data'][0]
                        if resource.realm == 'ticket':
                            ticket = Ticket(self.env, resource.id)
                            if components and \
                                    ticket.values['component'] in components:
                                filtered_events.append(event)
                    else:
                        filtered_events.append(event)
                data['events'] = filtered_events
        return template, data, content_type

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'timeline.html':
            # Insert the new field for entering user names
            filter = Transformer('//form[@id="prefs"]/fieldset')
            return stream | \
                   filter.before(html.br()) | \
                   filter.before(
                       html.label('Filter Components (none for all): ')) | \
                   filter.before(html.br()) | \
                   filter.before(self._components_field_input(req))
        return stream

    def _components_field_input(self, req):
        select = html.select(name='filter-components', id='filter-components',
                             multiple='multiple', size='10')
        selected_comps = req.args.getlist('filter-components')
        for component in self.env.db_query("""
                SELECT name FROM component ORDER BY name
                """):
            selected = 'selected' if component[0] in selected_comps else None
            select.append(html.option(component[0], value=component[0],
                                      selected=selected))
        return select
