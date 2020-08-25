# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2013 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann

from trac.config import Option
from trac.ticket.query import Query
from trac.util.text import to_unicode
from trac.wiki.api import parse_args

from wikicalendar.api import WikiCalendarBuilder


class WikiCalendarTicketProvider(WikiCalendarBuilder):
    """Custom TicketQuery macro implementation for WikiTicketCalendarMacro.

    Most lines were taken directly from that code.
    *** Original Comments as follows (shortend)***
    Macro that lists tickets that match certain criteria.

    This macro accepts a comma-separated list of keyed parameters,
    in the form "key=value".

    If the key is the name of a field, the value must use the syntax
    of a filter specifier as defined in TracQuery#QueryLanguage.
    Note that this is ''not'' the same as the simplified URL syntax
    used for `query:` links starting with a `?` character.

    In addition to filters, several other named parameters can be used
    to control how the results are presented. All of them are optional.

    Also, using "&" as a field separator still works but is deprecated.
    """

    def declare(self):
        return {
            'capability': ['harvest'],
            'resource': 'ticket',
            'target': 'body',
        }

    def harvest(self, req, content):
        """TicketQuery provider method."""
        query_string = content

        cols = '|'.join(['description', 'owner', 'status', 'summary'])

        # Options from old 'wikiticketcalendar' section have been migrated to
        # 'wikicalendar' configuration section.
        due_field = self.config.get('wikicalendar', 'ticket.due_field')
        if due_field:
            cols += '|' + due_field

        query_string += '&cols=%s' % cols
        query = Query.from_string(self.env, query_string)

        result = query.execute(req)
        while query.offset + query.max < query.num_items:
            query.offset += query.max
            result.extend(query.execute(req))

        tickets = [
            t for t in result if 'TICKET_VIEW' in req.perm('ticket', t['id'])
        ]

        return tickets
