# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 F@lk Brettschneider aka falkb
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Originally based on MilestoneQueryMacro code of Nic Ferrier.
#

import pkg_resources
from StringIO import StringIO
from datetime import datetime

from trac.util.datefmt import format_date, from_utimestamp, utc
from trac.util.html import Markup
from trac.wiki.formatter import Formatter
from trac.wiki.macros import WikiMacroBase


pkg_resources.require('Trac >= 1.0')


class UpcomingMilestonesChartMacro(WikiMacroBase):
    """Display a list of the latest upcoming milestones.

      [[UpcomingMilestonesChart(%-%,10,Next 10 Milestone Dates,yellow)]]

    The pattern is a SQL LIKE pattern.
    """

    def expand_macro(self, formatter, name, text):
        option_list = text.split(",")
        pattern, max_displayed, title, overdue_color = text.split(",")

        with self.env.db_query as db:
            milestone_names = [name for name, due in db("""
                    SELECT name, due FROM milestone
                    WHERE name %s AND completed = 0
                    ORDER BY due ASC
                    """ % db.like(), (pattern,))]
            milestone_dues = [due for due, in db("""
                    SELECT due FROM milestone
                    WHERE name %s AND completed = 0
                    ORDER BY due ASC
                    """ % db.like(), (pattern,))]

        out = StringIO()
        wikitext = "=== %s ===\n" % title
        cur_displayed = 0
        cur_idx = 0
        for m in milestone_names:
            if not max_displayed or cur_displayed < int(max_displayed):
                if milestone_dues[cur_idx]:
                    wikitext += """ * [[milestone:%s]]""" % m

                    date = "(%s)" % format_date(milestone_dues[cur_idx],
                                                tzinfo=formatter.req.tz,
                                                locale=formatter.req.locale)

                    if overdue_color and datetime.now(utc) > from_utimestamp(milestone_dues[cur_idx]):
                        wikitext += ' [[span(style=background-color: ' + overdue_color + ',' + date + ')]]'
                    else:
                        wikitext += ' ' + date
                    wikitext += '\n'
                    cur_displayed += 1
            cur_idx += 1
        Formatter(self.env, formatter.context).format(wikitext, out)

        return Markup(out.getvalue())
