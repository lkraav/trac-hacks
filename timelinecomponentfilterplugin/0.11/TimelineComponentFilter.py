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

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'timeline.html':
            components = req.args.get('filter-components')
            components = type(components) is unicode and \
                         (components,) or components
            if components:
                ticket_types = ('newticket', 'editedticket', 'closedticket',
                                'attachment', 'reopenedticket')
                filtered_events = []
                for event in data['events']:
                    if event['kind'] in ticket_types:
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
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM component ORDER BY name")
        select = html.select(name='filter-components', id='filter-components',
                             multiple='multiple', size='10')
        selected_comps = req.args.get('filter-components')
        selected_comps = type(selected_comps) is unicode and \
                         (selected_comps,) or selected_comps
        for component in cursor:
            if selected_comps and component[0] in selected_comps:
                select.append(html.option(component[0], value=component[0],
                                          selected="selected"))
            else:
                select.append(html.option(component[0], value=component[0]))
        return select
