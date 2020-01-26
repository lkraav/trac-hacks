# -*- coding: utf-8 -*-

from datetime import datetime

from trac.admin import *
from trac.core import *
from trac.util.datefmt import parse_date, utc, format_date
from trac.util.html import tag
from trac.web.chrome import Chrome, add_script, add_script_data
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

from timetracking.model import LogEntry, Task


def query_chart_data(env, kw):

    def kwlist(name):
        if name in kw:
            return [x for x in kw[name].split('|')]

    users = kwlist('user')
    categories = kwlist('category')
    projects = kwlist('project')
    tasks = kwlist('task')
    years = kwlist('year')

    where_clauses = []
    where_params = []
    xaxis_where_clauses = []
    xaxis_where_params = []
    if users:
        where_clauses.append('l.user in (%s)' % ','.join(['%s'] * len(users)))
        where_params.extend(users)
    if categories:
        where_clauses.append('t.category in (%s)' % ','.join(['%s'] * len(categories)))
        where_params.extend(categories)
    if projects:
        where_clauses.append('t.project in (%s)' % ','.join(['%s'] * len(projects)))
        where_params.extend(projects)
    if tasks:
        where_clauses.append('t.name in (%s)' % ','.join(['%s'] * len(tasks)))
        where_params.extend(tasks)
    if years:
        year_clause = 't.year in (%s)' % ','.join(['%s'] * len(years))
        where_clauses.append(year_clause)
        where_params.extend(years)
        xaxis_where_clauses.append(year_clause)
        xaxis_where_params.extend(years)

    if where_clauses:
        where_clause = 'WHERE ' + ' AND '.join(where_clauses)
    else:
        where_clause = ''

    if xaxis_where_clauses:
        xaxis_where_clause = 'WHERE ' + ' AND '.join(xaxis_where_clauses)
    else:
        xaxis_where_clause = ''

    mode = kw.get('mode', 'cumulative')
    join_operator = '>='
    if mode == 'activity':
        join_operator = '='

    rows = env.db_transaction("""
            SELECT xaxis.date, COALESCE(SUM(cumulative.spent_hours), 0)
            FROM (
                SELECT DISTINCT l.date as date
                FROM timetrackinglogs l
                INNER JOIN timetrackingtasks t ON l.task_id = t.id
                %s
            ) xaxis
            LEFT OUTER JOIN (
                SELECT l.date as date, l.spent_hours as spent_hours
                FROM timetrackinglogs l
                INNER JOIN timetrackingtasks t ON l.task_id = t.id
                %s
            ) cumulative ON xaxis.date %s cumulative.date
            GROUP BY xaxis.date
            ORDER BY xaxis.date
            """ % (xaxis_where_clause, where_clause, join_operator), xaxis_where_params + where_params)
    ld = [(format_date(date), cumulative_spent_hours) for date, cumulative_spent_hours in rows]
    return ([label for label, value in ld],
            [value for label, value in ld])


class TimeTrackingChartMacro(WikiMacroBase):
    """Show a chart of the time tracking data.
   
    The arguments are:
    * `width`: Width of the chart. (Defaults to 1200.)
    * `height`: Height of the chart. (Defaults to 600.)
    * `user`: `|`-separated list of users. (Defaults to all users.)
    * `category`: `|`-separated list of categories. (Defaults to all categories.)
    * `project`: `|`-separated list of projects. (Defaults to all projects.)
    * `task`: `|`-separated list of tasks. (Defaults to all tasks.)
    * `year`: `|`-separated list of years. (Defaults to all years.)
    * `mode`: `cumulative` or `activity`. (Defaults to cumulative.)

    Example:
    {{{
        [[TimeTrackingChart(year=2014,user=peter)]]
    }}}
    """

    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)
        args = [arg.strip() for arg in args]

        width = int(kw.get('width', 1200))
        height = int(kw.get('height', 600))

        req = formatter.req
        context = formatter.context

        r = query_chart_data(self.env, kw)

        chart_data = {

            'data': {
                'x': r[0],
                'y': r[1],
                'type': 'line',
                'mode': 'lines+markers',
                'fill': 'tozeroy',
            },

            'layout': {
                'width': width,
                'height': height,
                'margin': {
                    'r': 0,
                    't': 0,
                },
            },

            'options': {
                'displayModeBar': False,
                'staticPlot': False, 
            },
        }
        chart_data_id = '%012x' % id(chart_data)
        
        add_script(req, 'timetracking/plotly-basic.min.js')
        add_script(req, 'timetracking/timetrackingchart.js')
        add_script_data(req, {'timetracking_chart_%s' % chart_data_id: chart_data})

        return tag.div("Enable JavaScript to display the time tracking chart.",
            class_='trac-timetracking-chart system-message',
            id='trac-timetracking-chart-%s' % chart_data_id)
