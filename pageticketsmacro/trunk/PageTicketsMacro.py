import re

from trac.core import *
from trac.wiki.api import parse_args
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase

author = "Lucid"
version = "1.0 ($Rev$)"
license = "BSD"
url = "https://trac-hacks.org/wiki/PageTicketsMacro"


class PageTicketsMacro(WikiMacroBase):
    """Expands to a TicketQuery of all tickets mentioned in the current wiki text.

    All parameters are passed to TicketQuery. Format defaults to table.

    Examples:
    {{{
    All tickets mentioned on this page:
    [[PageTickets()]]

    New tickets mentioned on this page, grouped by milestone:
    [[PageTickets(status=new,group=milestone)]]
    }}}
    """

    tickets_re = re.compile("""
        (?:
            \#           # #
            |            # OR
            ticket:      # ticket:
            |            # OR
            issue:       # issue:
            |            # OR
            bug:         # bug:
        )
        (\d+)            # Group 1: The ticket number
    """, re.VERBOSE)

    def expand_macro(self, formatter, name, content, args):
        tickets = PageTicketsMacro.tickets_re.findall(formatter.source)
        args, kw = parse_args(content)
        if 'id' in kw:
            tickets.append(kw['id'])
        if not tickets:
            return 'No tickets found'
        kw['id'] = '|'.join(tickets)
        kw.setdefault('format', 'table')
        args = args + ['%s=%s' % (k, v) for k, v in kw.items()]
        query = '[[TicketQuery(%s)]]' % ','.join(args)
        return format_to_html(self.env, formatter.context, query)
