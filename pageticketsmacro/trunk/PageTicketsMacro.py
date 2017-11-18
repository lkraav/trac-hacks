import re

from trac.core import *
from trac.wiki.api import parse_args
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

author = "Lucid"
version = "1.0 ($Rev$)"
license = "BSD"
url = "https://trac-hacks.org/wiki/PageTicketsMacro"


class PageTicketsMacro(WikiMacroBase):
    """Expands to a TicketQuery of all tickets mentioned in the current wiki page.

    All parameters are passed to TicketQuery. Format defaults to table.

    Examples:
    {{{
    All tickets mentioned on this page:
    [[PageTickets()]]

    New tickets mentioned on this page, grouped by milestone:
    [[PageTickets(status=new,group=milestone)]]
    }}}
    """

    tickets_re = re.compile('(?:#|(?:ticket:|bug:))(\d+)')

    def expand_macro(self, formatter, name, content, args):
        if not formatter.resource or not formatter.resource.realm == 'wiki':
            raise TracError('PageTicketsMacro only works on wiki pages')
        pagename = formatter.resource.id
        page = WikiPage(self.env, pagename)
        tickets = PageTicketsMacro.tickets_re.findall(page.text)
        if not tickets:
            return 'No tickets found'
        args, kw = parse_args(content)
        kw['id'] = '|'.join(tickets)
        kw.setdefault('format', 'table')
        args = args + ['%s=%s' % (k, v) for k, v in kw.items()]
        query = '[[TicketQuery(%s)]]' % ','.join(args)
        return format_to_html(self.env, formatter.context, query)
