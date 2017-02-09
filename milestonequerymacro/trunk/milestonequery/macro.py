# -*- coding: utf-8 -*-

import StringIO

from trac.util.html import Markup
from trac.wiki.formatter import Formatter
from trac.wiki.macros import WikiMacroBase, parse_args


class MilestoneQueryMacro(WikiMacroBase):
    """Display a ticket query based on the milestone name for each
    matching milestone.

    Specify a pattern to match the milestones and optionally
    'completed' and 'desc' (or 'asc' which is the default):

      [[MilestoneQuery(rc_%)]]

      [[MilestoneQuery(release_%, completed)]]

      [[MilestoneQuery(release_%, completed, DESC)]]

    The pattern is a SQL LIKE pattern.
    """

    def expand_macro(self, formatter, name, content, args=None):
        pargs, kwargs = parse_args(content)
        pattern = pargs[0]
        if len(pargs) > 1 and pargs[1].strip().upper() == "COMPLETED":
            completed = "AND completed>0"
        else:
            completed = "AND completed=0"
        if len(pargs) > 2 and pargs[2].strip().upper() == "ASC":
            ordering = "ASC"
        else:
            ordering = "DESC"

        out = StringIO.StringIO()
        with self.env.db_query as db:
            for name, in db("""
                    SELECT name FROM milestone
                    WHERE name %s %s ORDER BY name %s
                    """ % (db.like(), completed, ordering), (pattern,)):
                wikitext = """
                    == [milestone:%(milestonename)s %(milestonename)s]
                    [[TicketQuery(milestone=%(milestonename)s,order=id,desc=0,format=table,col=summary|owner|ticket_status|type|status)]]
                    """ % {'milestonename': name}
                Formatter(self.env, formatter.context).format(wikitext, out)

        return Markup(out.getvalue())


