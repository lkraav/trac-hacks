# -*- coding: utf-8 -*-

from __future__ import division

import datetime
import math
from functools import reduce

from trac.core import *
from trac.util.datefmt import parse_date, utc
from trac.util.html import tag
from trac.web.chrome import (Chrome, add_script, add_script_data,
                             add_stylesheet, ITemplateProvider)
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

from weekplan.core import WeekPlanModule


class WeekPlanMacro(WikiMacroBase):
    """Show a week-by-week calendar and allow planning events.
   
    The arguments are:
    * `plan`: Id of the shown collection of events. (required)
      * Can be a `|`-separated list of multiple plans.
    * `start`: A date  in the first week shown. (Defaults to today.)
    * `weeks`: Number of weeks shown. (Defaults to one.)
    * `weeksperrow`: Number of weeks per row. (Defaults to one.)
    * `width`: Width of the calendar. (Defaults to 400.)
    * `rowheight`: Height of one row of the calendar. (Defaults to 100.)
    * `showweekends`: Show Saturdays and Sundays (Defaults to hidden.)
    * `color`: Color of the events. (Defaults to `#3A87AD|#39AC60|#D7A388|#88BDD7|#9939AC|#AC9939`.)
      * Can be a `|`-separated list of multiple colors. Each plan uses a different colors if multiple plans are specified.
    * `label`: Labels shown instead of the plan ids. (Defaults to the plan ids.)
      * Can be a `|`-separated list of multiple labels. Each plan uses a different label if multiple plans are specified.
    * `hidelegend`: Show a legend below the calendar. (Defaults to shown.)
    Example:
    {{{
        [[WeekPlan(plan=example, start=1.1.2014,weeks=10)]]
    }}}
    """

    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)
        args = [arg.strip() for arg in args]

        plan_ids = kw.get('plan', '').split('|')
        if not plan_ids:
            raise TracError('Missing plan id')

        colors = kw.get('color', '#38A|#4B6|#DA8|#9CD|#CAD|#CC7').split('|')
        colors = dict(zip(plan_ids, colors*((len(plan_ids)-1)//len(colors)+1)))

        labels = [label for label in kw.get('label', '').split('|') if label]
        labels = dict(zip(plan_ids, labels + plan_ids[len(labels):]))

        start = kw.get('start')
        if start is None:
            start = datetime.date.today()
        else:
            start = parse_date(start, utc).date()
        weeks = int(kw.get('weeks', 1))
        weeksperrow = int(kw.get('weeksperrow', 1))

        width = int(kw.get('width', 400))
        rowheight = int(kw.get('rowheight', 100))

        req = formatter.req
        context = formatter.context
        core = WeekPlanModule(self.env)

        plan_data = {
            'form_token': req.form_token,
            'api_url': formatter.href('weekplan'),
            'plans': plan_ids,
            'plans_with_add_event': [plan_id for plan_id in plan_ids if core.can_plan_add_event(plan_id)],
            'plans_with_update_event': [plan_id for plan_id in plan_ids if core.can_plan_update_event(plan_id)],
            'plans_with_delete_event': [plan_id for plan_id in plan_ids if core.can_plan_delete_event(plan_id)],
            'colors': colors,
            'labels': labels,
            'calendar_data': {
                'firstDay': 1, # Start weeks on Monday
                'weekends': 'showweekends' in args, # Hide Saturdays and Sundays by default
                'columnFormat': 'ddd', # Show column headers "Mon Tue Wed Thu Fri"
                'defaultView': 'multiWeek', # Custom extension of "basicWeek" view!
                'defaultDate': start.isoformat(),
                'weeks': weeks, # New option for custom "multiWeek" view
                'weeksperrow': weeksperrow, # New option for custom "multiWeek" view
                'contentHeight': math.ceil(weeks / weeksperrow) * rowheight,
                'header': { # Title and navigation buttons 
                    'left': '',
                    'center': 'title',
                    'right': 'prev,next'
                },
                'eventSources': [
                    {
                        'url': formatter.href('weekplan'),
                        'data': {
                            'format': 'json',
                            'plan': '|'.join(plan_ids),
                        },
                    },
                ],
            },
        }
        plan_data_id = '%012x' % id(plan_data)
        
        add_stylesheet(req, 'weekplan/css/fullcalendar.css')
        add_script(req, 'weekplan/js/moment.min.js')
        add_script(req, 'weekplan/js/fullcalendar.js')
        add_script(req, 'weekplan/js/weekplan.js')
        add_script_data(req, {'weekplan_%s' % plan_data_id: plan_data})
        Chrome(self.env).add_jquery_ui(req)
        
        calendar_element = tag.div("Enable JavaScript to display the week plan.",
            class_='trac-weekplan system-message',
            id='trac-weekplan-%s' % plan_data_id,
            style='width:%spx' % width)
        if 'hidelegend' in args:
            return calendar_element
        else:
            return tag.div(
                calendar_element,
                self._render_legend(plan_ids, labels, colors))

    def _render_legend(self, names, labels, colors):
        def merge(a, b):
            return a + u' | ' + b
        items = [tag.span(u'■', style='color:%s' % colors[name]) + ' ' + labels[name] for name in names]
        return tag.p(
            reduce(merge, items),
            class_='trac-weekplan-legend')
