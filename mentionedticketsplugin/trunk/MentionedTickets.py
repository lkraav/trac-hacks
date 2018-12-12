import re

from trac.core import *
from trac.util.html  import tag
from trac.web.api import IRequestFilter

author = "Lucid"
version = "1.0 ($Rev$)"
license = "BSD"
url = "https://trac-hacks.org/wiki/MentionedTicketsPlugin" 


class MentionedTickets(Component):
    """List all tickets mentioned in the current ticket."""

    implements(IRequestFilter)

    tickets_re = re.compile('(?:#|(?:ticket:|issue:|bug:))(\d+)')

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        path = req.path_info
        if path.startswith('/ticket/'):
            if data and 'ticket' in data and 'fields' in data:
                self._append_related_tickets(req, data)
        return template, data, content_type

    def _append_related_tickets(self, req, data):
        rendered = ''
        ticket = data['ticket']
        comments = [c[4] for c in ticket.get_changelog()
                         if c[2] == 'comment']
        wiki_fields = [field['name'] for field in ticket.fields
                                     if field.get('format') == 'wiki']
        values = [ticket[name] for name in wiki_fields] + comments
        mentions = [int(match) for value in values
                               if value is not None
                               for match in MentionedTickets.tickets_re.findall(value)]
        if mentions:
            ticket.values['Mentioned Tickets'] = True # Activates field
            results = []
            for id in sorted(set(mentions)):
                label = '#%s' % (id,)
                href = req.href.ticket(id)
                link = tag.a(label, href=href)
                results.append(link)
            rendered = tag.span(*[e for pair in zip(results, [' '] * len(results)) for e in pair][:-1])
        data['fields'].append({
            'name': 'Mentioned Tickets',
            'rendered': rendered,
            'type': 'textarea', # Full row
        })
