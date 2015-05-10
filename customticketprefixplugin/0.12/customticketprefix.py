# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc/Cinc-th
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from trac.config import ListOption
from trac.core import Component, implements
from trac.util import Ranges, shorten_line
from trac.wiki import IWikiSyntaxProvider

version = "1.0.0"
url = "http://trac-hacks.org/wiki/CustomTicketPrefixPlugin"
license = "3-Clause BSD"
author = 'Cinc/Cinc-th'

class CustomTicketPrefix(Component):
    """Define prefixes to group tickets.

    ===  ===
    A list of prefixes can be defined in ''trac.ini'' to form ticket groups:
    {{{
    [ticket-prefix]
    prefix = Pre1, Foo, BAR, ...
    }}}

    Note that the prefix is case sensitive.

    Specify a ticket like {{{PREFIX:#1234}}} similar to intertrac links. The difference is it will be rendered like
    normal TracLinks with the proper hint holding ticket information instead of InterTrac information.
    Closed tickets will be rendered properly as strike through.

    This is useful if you have several Trac instances referencing the same repository. By defining different prefixes
    for each instance it is possible to reference the correct instance in the commit message. For example:
    {{{
    Foo:#123: fix for encoding error in function bar().
    }}}
    In the repo browser of Trac instance 'Foo' the link is rendered correctly and shows the ticket status from the
    commit message.

    Prefixes of other instances may be defined in instance 'Foo' as usual as intertrac links.
    """
    implements(IWikiSyntaxProvider)

    prefixes = ListOption("ticket-prefix", 'prefix', '', doc="List of prefixes defining ticket "
                                                             "groups. Specify a ticket like "
                                                             "''PREFIX:#1234'' similar to InterTrac "
                                                             "links. The difference is it will be "
                                                             "rendered similar to normal TracLinks "
                                                             "with the proper hint holding ticket information "
                                                             "instead of InterTrac information. Closed tickets will "
                                                             "be rendered properly as strike through. This is useful "
                                                             "if you have several Trac instances referencing the same "
                                                             "repository. By defining different prefixes for each "
                                                             "instance it is possible to reference the correct instance "
                                                             "in the commit message. Prefixes of other instances may "
                                                             "be defined as InterTrac links as usual.")

    # Taken from ticket\api.py
    def format_summary(self, summary, status=None, resolution=None, type=None):
        summary = shorten_line(summary)
        if type:
            summary = type + ': ' + summary
        if status:
            if status == 'closed' and resolution:
                status += ': ' + resolution
            return "%s (%s)" % (summary, status)
        else:
            return summary

    # IWikiSyntaxProvider methods

    def get_link_resolvers(self):
        return []

    def get_wiki_syntax(self):

        for p in self.prefixes:
            yield (
                r"%s:#%s" % (p, Ranges.RE_STR),
                lambda x, y, z: self._format_link(x, 'ticket', y.split(':')[1][1:], y, z)
            )

    # Taken from Trac ticket\api.py
    def _format_link(self, formatter, ns, target, label, fullmatch=None):

        intertrac = formatter.shorthand_intertrac_helper(ns, target, label,
                                                         fullmatch)
        if intertrac:
            return intertrac
        try:
            link, params, fragment = formatter.split_link(target)
            r = Ranges(link)
            if len(r) == 1:
                num = r.a
                ticket = formatter.resource('ticket', num)
                from trac.ticket.model import Ticket
                if Ticket.id_is_valid(num) and \
                        'TICKET_VIEW' in formatter.perm(ticket):
                    # TODO: watch #6436 and when done, attempt to retrieve
                    #       ticket directly (try: Ticket(self.env, num) ...)
                    cursor = formatter.db.cursor()
                    cursor.execute("SELECT type,summary,status,resolution "
                                   "FROM ticket WHERE id=%s", (str(num),))
                    for type, summary, status, resolution in cursor:
                        title = self.format_summary(summary, status,
                                                    resolution, type)
                        href = formatter.href.ticket(num) + params + fragment
                        return tag.a(label, class_='%s ticket' % status,
                                     title=title, href=href)
            else:
                ranges = str(r)
                if params:
                    params = '&' + params[1:]
                return tag.a(label, title='Tickets '+ranges,
                             href=formatter.href.query(id=ranges) + params)
        except ValueError:
            pass
        return tag.a(label, class_='missing ticket')