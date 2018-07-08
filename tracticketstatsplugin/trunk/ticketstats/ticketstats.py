# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2009 Prentice Wongvibulsin <me@prenticew.com>
# Copyright (c) 2010-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import json
import re
from datetime import date, datetime, time, timedelta

from trac.config import IntOption, Option
from trac.core import Component, implements
from trac.ticket import Milestone
from trac.ticket import Component as TicketComponent
from trac.util.datefmt import format_date, parse_date, to_utimestamp, utc
from trac.util.html import tag
from trac.web.api import IRequestHandler
from trac.web.chrome import (
    Chrome, INavigationContributor, ITemplateProvider, add_script_data)

DEFAULT_DAYS_BACK = 30 * 6
DEFAULT_INTERVAL = 30


class TicketStatsPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    plotly_js_url = Option('ticketstats', 'plotly_js_url',
                           default='//cdn.plot.ly/plotly-latest.min.js',
                           doc='Location of plotly.js')

    default_days_back = IntOption('ticketstats', 'default_days_back',
                                  default=DEFAULT_DAYS_BACK,
                                  doc='Number of days to show by default')

    default_interval = IntOption('ticketstats', 'default_interval',
                                 default=DEFAULT_INTERVAL,
                                 doc='Number of days between each data point'
                                     ' (interval) by default')

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'ticketstats'

    def get_navigation_items(self, req):
        if 'TICKET_VIEW' in req.perm:
            yield ('mainnav', 'ticketstats',
                   tag.a('Ticket Stats', href=req.href.ticketstats()))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/ticketstats', req.path_info)

    def process_request(self, req):
        req.perm.require('TICKET_VIEW')

        interval = req.args.getint('interval', self.default_interval)

        todays_date = date.today()
        at_date = req.args.get('end_date')
        if at_date:
            at_date = parse_date(at_date)
            at_date = datetime.combine(at_date, time(11, 59, 59, 0, utc))
        else:
            at_date = datetime.combine(todays_date, time(11, 59, 59, 0, utc))

        from_date = req.args.get('start_date')
        if from_date:
            from_date = parse_date(from_date)
            from_date = datetime.combine(from_date, time(0, 0, 0, 0, utc))
        else:
            from_date = at_date - timedelta(self.default_days_back)

        milestone = req.args.get('milestone')
        if milestone == '__all':
            milestone = None
        component = req.args.get('component')
        if component == '__all':
            component = None

        count = self._get_ticket_counts(from_date, at_date, interval,
                                        milestone, component)
        x = [c['date'] for c in count]
        ticket_data = [
            {
                'x': x,
                'y': [c['new'] for c in count],
                'name': 'open',
                'type': 'bar',
            },
            {
                'x': x,
                'y': [c['closed'] for c in count],
                'name': 'closed',
                'type': 'bar',
            },
            {
                'x': x,
                'y': [c['open'] for c in count],
                'name': 'open',
                'type': 'scatter',
            },
        ]

        if req.is_xhr:
            req.send(json.dumps(ticket_data))

        show_all = req.args.get('show') == 'all'
        milestone_list = [m.name for m in Milestone.select(self.env, show_all)]
        component_list = [c.name for c in TicketComponent.select(self.env)]

        add_script_data(req, {
            'base_url': req.base_url,
            'ticket_data': ticket_data,
        })
        Chrome(self.env).add_jquery_ui(req)

        return 'ticketstats.html', {
            'start_date': from_date,
            'end_date': at_date,
            'components': component_list,
            'milestones': milestone_list,
            'interval_selected': interval,
            'milestone_selected': milestone,
            'component_selected': component,
            'plotly_js_url': self.plotly_js_url,
        }, None

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _get_ticket_counts(self, from_date, at_date, graph_res, milestone,
                           component):

        counts = []

        # Calculate 0th point
        last_date = from_date - timedelta(graph_res)
        last_num_open = get_num_open_tix(self.env, last_date, milestone,
                                         component)

        # Calculate remaining points
        for cur_date in date_range(from_date, at_date, graph_res):
            num_open = get_num_open_tix(self.env, cur_date, milestone,
                                        component)
            num_closed = get_num_closed_tix(self.env, last_date, cur_date,
                                            milestone, component)
            date_str = format_date(cur_date)
            if graph_res != 1:
                date_str = "%s thru %s" % (format_date(last_date), date_str)
            counts.append({
                'date': date_str,
                'new': num_open - last_num_open + num_closed,
                'closed': num_closed,
                'open': num_open
            })
            last_num_open = num_open
            last_date = cur_date

        return counts


def get_num_closed_tix(env, from_date, at_date, milestone, component):
    """Returns an integer of the number of close ticket events counted
    between from_date to at_date."""

    args = [to_utimestamp(from_date), to_utimestamp(at_date)]
    milestone_str = ''

    if milestone:
        args.append(milestone)
        milestone_str += 'AND t.milestone = %s'

    component_str = ''
    if component:
        args.append(component)
        component_str += 'AND t.component = %s'

    # Count tickets between two dates (note: does not account for tickets
    # that were closed and then reopened between the two dates)
    closed_count = 0
    for status, in env.db_query("""
            SELECT newvalue
            FROM ticket_change tc
            INNER JOIN ticket t ON t.id = tc.ticket AND tc.time > %%s
              AND tc.time <= %%s AND tc.field = 'status' %s %s
            ORDER BY tc.time
            """ % (milestone_str, component_str), args):
        if status == 'closed':
            closed_count += 1

    return closed_count


def get_num_open_tix(env, at_date, milestone, component):
    """Returns an integer of the number of tickets currently open on that
    date."""

    args = [to_utimestamp(at_date)]
    milestone_str = ''
    if milestone:
        args.append(milestone)
        milestone_str += 'AND t.milestone = %s'

    # Filter by component if component is selected
    component_str = ''
    if component:
        args.append(component)
        component_str += 'AND t.component = %s'

    # Count number of tickets created before specified date
    open_count = 0
    for open_count, in env.db_query("""
            SELECT COUNT(*) FROM ticket t
            WHERE t.time <= %%s %s %s
            """ % (milestone_str, component_str), args):
        break

    # Count closed and reopened tickets
    for status, in env.db_query("""
            SELECT newvalue
            FROM ticket_change tc
            INNER JOIN ticket t ON t.id = tc.ticket AND tc.time > 0
             AND tc.time <= %%s AND tc.field = 'status' %s %s
            ORDER BY tc.time
            """ % (milestone_str, component_str), args):
        if status == 'closed':
            open_count -= 1
        elif status == 'reopened':
            open_count += 1

    return open_count


def date_range(begin, end, delta=timedelta(1)):
    """Stolen from:
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/574441

    Form a range of dates and iterate over them.

    Arguments:
    begin -- a date (or datetime) object; the beginning of the range.
    end   -- a date (or datetime) object; the end of the range.
    delta -- (optional) a timedelta object; how much to step each iteration.
             Default step is 1 day.

    Usage:

    """
    if not isinstance(delta, timedelta):
        delta = timedelta(delta)

    ZERO = timedelta(0)

    if begin < end:
        if delta <= ZERO:
            raise StopIteration
        test = end.__gt__
    else:
        if delta >= ZERO:
            raise StopIteration
        test = end.__lt__

    while test(begin):
        yield begin
        begin += delta
