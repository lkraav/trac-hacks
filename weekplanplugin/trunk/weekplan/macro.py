# -*- coding: utf-8 -*-

import pkg_resources
import datetime
import re

from genshi.builder import tag

from trac.core import *
from trac.util.datefmt import parse_date
from trac.web.chrome import (Chrome, add_script, add_script_data,
                             add_stylesheet, ITemplateProvider)
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

from weekplan.model import WeekPlanEvent


class WeekPlanMacro(WikiMacroBase):
    """Show a week-by-week calendar and allow planning events.
   
    The arguments are:
    * `plan`: Id of the shown collection of events. (required)
      * Can be a `|`-separated list of multiple plans.
    * `start`: A date  in the first week shown. (Defaults to today.)
    * `weeks`: Number of weeks shown. (Defaults to one.)
    * `width`: Width of the calendar. (Defaults to 400)
    * `rowheight`: Height of one row of the calendar. (Defaults to 100)
    * `showweekends`: Show Saturdays and Sundays (Default is hidden)
    * `color`: Color of the events. (Defaults to #3A87AD|#39AC60|#D7A388|#88BDD7|#9939AC|#AC9939)
      * Can be a `|`-separated list of multiple colors. Each plan uses a different colors if multiple plans are specified.
    * `format`: One of the following formatting modes:
      * `multiweek`: A multi-week calendar. (The default)
      * `count`: A simple count of events.
    * `matchtitle`: A regexp that matches event titles. (Defaults to match all events.)
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

        colors = kw.get('color', '#3A87AD|#39AC60|#D7A388|#88BDD7|#9939AC|#AC9939').split('|')
        colors = dict(zip(plan_ids, colors*((len(plan_ids)-1)/len(colors)+1)))
        def colorize(serialized_event):
            serialized_event['color'] = colors[serialized_event['plan']]
            return serialized_event

        start = kw.get('start')
        if start is None:
            start = datetime.datetime.today()
        else:
            start = parse_date(start)
        weeks = int(kw.get('weeks', 1))

        width = int(kw.get('width', 400))
        rowheight = int(kw.get('rowheight', 100))
        
        events = WeekPlanEvent.select_by_plans(self.env, plan_ids)

        if 'matchtitle' in kw:
            matchtitle_re = re.compile(kw.get('matchtitle'))
            events = [e for e in events if matchtitle_re.search(e.title)]

        format = kw.get('format', 'multiweek')
        if format == 'count':
            return tag.span(len(events))

        req = formatter.req
        context = formatter.context

        plan_data = {
            'form_token': req.form_token,
            'api_url': formatter.href('weekplan'),
            'plans': plan_ids,
            'colors': colors,
            'calendar_data': {
                'firstDay': 1, # Start weeks on Monday
                'weekends': 'showweekends' in args, # Hide Saturdays and Sundays by default
                'columnFormat': 'ddd', # Show column headers "Mon Tue Wed Thu Fri"
                'defaultView': 'multiWeek', # Custom extension of "basicWeek" view!
                'year': start.year,
                'month': start.month - 1, # 1-based months (January==1) to 0-based months (January==0)
                'date': start.day,
                'weeks': weeks, # New option for custom "multiWeek" view
                'contentHeight': weeks * rowheight,
                'header': { # Title and navigation buttons 
                    'left': '',
                    'center': 'title',
                    'right': 'prev,next'
                },
                'events': [ colorize(e.serialized(self.env, context)) for e in events],
            },
        }
        plan_data_id = '%012x' % id(plan_data)
        
        add_script(req, 'weekplan/js/fullcalendar.js')
        add_script(req, 'weekplan/js/weekplan.js')
        add_script_data(req, {'weekplan_%s' % plan_data_id: plan_data})
        add_stylesheet(req, 'weekplan/css/fullcalendar.css')
        Chrome(self.env).add_jquery_ui(req)
        
        return tag.div("Enable JavaScript to display the week plan.",
                    class_='trac-weekplan system-message',
                    id='trac-weekplan-%s' % plan_data_id,
                    style='width:%spx' % width)
