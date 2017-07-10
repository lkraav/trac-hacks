# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2009 Prentice Wongvibulsin <me@prenticew.com>
# Copyright (c) 2010-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
from datetime import date, datetime, time, timedelta

from genshi.builder import tag
from trac.config import IntOption, Option
from trac.core import Component, TracError, implements
from trac.ticket import Milestone
from trac.ticket import Component as TicketComponent
from trac.util.datefmt import format_date, parse_date, to_utimestamp, utc
from trac.web.api import IRequestHandler
from trac.web.chrome import Chrome, INavigationContributor, ITemplateProvider

# ************************
DEFAULT_DAYS_BACK = 30 * 6
DEFAULT_INTERVAL = 30
# ************************


class TicketStatsPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    yui_base_url = Option('ticketstats', 'yui_base_url',
                          default='//cdnjs.cloudflare.com/ajax/libs/yui/2.9.0',
                          doc='Location of YUI API')

    default_days_back = IntOption('ticketstats', 'default_days_back',
                                  default=DEFAULT_DAYS_BACK,
                                  doc='Number of days to show by default')

    default_interval = IntOption('ticketstats', 'default_interval',
                                 default=DEFAULT_INTERVAL,
                                 doc='Number of days between each data point'
                                     ' (resolution) by default')

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'ticketstats'

    def get_navigation_items(self, req):
        if 'TICKET_VIEW' in req.perm:
            yield ('mainnav', 'ticketstats',
                   tag.a('Ticket Stats', href=req.href.ticketstats()))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/ticketstats(?:_trac)?(?:/.*)?$', req.path_info)

    def process_request(self, req):
        req.perm.require('TICKET_VIEW')
        req_content = req.args.get('content')
        milestone = None
        component = None

        if None not in [req.args.get('end_date'), req.args.get('start_date'),
                        req.args.get('resolution')]:
            # form submit
            grab_at_date = req.args.get('end_date')
            grab_from_date = req.args.get('start_date')
            grab_resolution = req.args.get('resolution')
            grab_milestone = req.args.get('milestone')
            grab_component = req.args.get('component')

            if grab_milestone == "__all":
                milestone = None
            else:
                milestone = grab_milestone

            if grab_component == "__all":
                component = None
            else:
                component = grab_component

            # validate inputs
            if None in [grab_at_date, grab_from_date]:
                raise TracError('Please specify a valid range.')

            if None in [grab_resolution]:
                raise TracError('Please specify the graph interval.')

            if 0 in [len(grab_at_date), len(grab_from_date),
                     len(grab_resolution)]:
                raise TracError(
                    'Please ensure that all fields have been filled in.')

            if not grab_resolution.isdigit():
                raise TracError(
                    'The graph interval field must be an integer, days.')

            at_date = parse_date(grab_at_date)
            at_date = datetime.combine(at_date,
                                       time(11, 59, 59, 0, utc))  # Add tzinfo

            from_date = parse_date(grab_from_date)
            from_date = datetime.combine(from_date,
                                         time(0, 0, 0, 0, utc))  # Add tzinfo

            graph_res = int(grab_resolution)
        else:
            # default data
            todays_date = date.today()
            at_date = datetime.combine(todays_date, time(11, 59, 59, 0, utc))
            from_date = at_date - timedelta(self.default_days_back)
            graph_res = self.default_interval

        count = []

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
            count.append({'date': date_str,
                          'new': num_open - last_num_open + num_closed,
                          'closed': num_closed,
                          'open': num_open})
            last_num_open = num_open
            last_date = cur_date

        # if chart data is requested, raw text is returned rather than data
        # object for templating
        if req_content is not None and req_content == "chartdata":
            js_data = '{"chartdata": [\n'
            for x in count:
                js_data += '{"date": "%s",' % x['date']
                js_data += ' "new_tickets": %s,' % x['new']
                js_data += ' "closed": %s,' % x['closed']
                js_data += ' "open": %s},\n' % x['open']
            js_data = js_data[:-2] + '\n]}'
            req.send(js_data.encode('utf-8'))
            return
        else:
            show_all = req.args.get('show') == 'all'
            milestone_list = [m.name for m in
                              Milestone.select(self.env, show_all)]

            # Get list of all components
            component_list = [c.name
                              for c in TicketComponent.select(self.env)]
            if milestone in milestone_list:
                milestone_num = milestone_list.index(milestone) + 1
            else:
                milestone_num = 0

            # index of selected component
            if component in component_list:
                component_num = component_list.index(component) + 1
            else:
                component_num = 0

            data = {
                'ticket_data': count,
                'start_date': format_date(from_date),
                'end_date': format_date(at_date),
                'resolution': str(graph_res),
                'baseurl': req.base_url,
                'components': component_list,
                'milestones': milestone_list,
                'cmilestone': milestone_num,
                'ccomponent': component_num,
                'yui_base_url': self.yui_base_url.rstrip('/'),
                'debug': 'debug' in req.args
            }

            if hasattr(Chrome, 'add_jquery_ui'):
                Chrome(self.env).add_jquery_ui(req)

            return 'ticketstats.html', data, None

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


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
