import re
from trac.core import *
from tractags.api import ITagProvider
from trac.ticket.model import Ticket
from trac.util.text import to_unicode
from trac.util.compat import set, sorted
from trac.config import ListOption
from trac.resource import Resource


class TicketTagProvider(Component):
    """A tag provider using ticket fields as sources of tags.

    Currently does NOT support custom fields.
    """
    implements(ITagProvider)

    fields = ListOption('tags', 'ticket_fields', 'keywords',
        doc='List of ticket fields to expose as tags.')

#    custom_fields = ListOption('tags', 'custom_ticket_fields',
#        doc='List of custom ticket fields to expose as tags.')

    _keyword_split = re.compile(r'''\w[\w.@-]+''', re.UNICODE)

    # ITagProvider methods
    def get_taggable_realm(self):
        return 'ticket'

    def get_tagged_resources(self, req, tags):
        if 'TICKET_VIEW' not in req.perm:
            return
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        args = []
        sql = "SELECT * FROM (SELECT id, %s, %s AS fields FROM ticket) s" % (','.join(self.fields),
            '||'.join(["COALESCE(%s, '')" % f for f in self.fields]))
        constraints = []
        if tags:
            constraints.append(
                "(" + ' OR '.join(["fields LIKE %s" for t in tags]) + ")")
            args += ['%' + t + '%' for t in tags]
        else:
            constraints.append("fields != ''")

        if constraints:
            sql += " WHERE " + " AND ".join(constraints)
        sql += " ORDER BY id"
        cursor.execute(sql, args)
        for row in cursor:
            id, ttags = row[0], ' '.join([f for f in row[1:-1] if f])
            perm = req.perm('ticket', id)
            if 'TICKET_VIEW' not in perm or 'TAGS_VIEW' not in perm:
                continue
            ticket_tags = set(self._keyword_split.findall(ttags))
            tags = set([to_unicode(x) for x in tags])
            if (not tags or ticket_tags.intersection(tags)):
                yield Resource('ticket', id), ticket_tags


    def get_resource_tags(self, req, resource):
        if 'TICKET_VIEW' not in req.perm(resource):
            return
        ticket = Ticket(self.env, resource.id)
        return self._ticket_tags(ticket)

    def set_resource_tags(self, req, resource, tags):
        req.perm.require('TICKET_MODIFY', resource)
        ticket = Ticket(self.env, resource.id)
        all = self._ticket_tags(ticket)
        keywords = set(self._keyword_split.findall(ticket['keywords']))
        tags.difference_update(all.difference(keywords))
        ticket['keywords'] = u' '.join(sorted(map(to_unicode, tags)))
        ticket.save_changes(req.username, u'')

    def remove_resource_tags(self, req, resource):
        req.perm.require('TICKET_MODIFY', resource)
        ticket = Ticket(self.env, resource.id)
        ticket['keywords'] = u''
        ticket.save_changes(req.username, u'')

    # Private methods
    def _ticket_tags(self, ticket):
        return set(self._keyword_split.findall(
            ' '.join(filter(None, [ticket[f] for f in self.fields]))))
