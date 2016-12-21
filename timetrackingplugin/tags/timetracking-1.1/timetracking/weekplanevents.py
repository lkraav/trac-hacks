# -*- coding: utf-8 -*-

from trac.core import *
from trac.util.datefmt import from_utimestamp, to_utimestamp

from timetracking.model import Task, LogEntry

from weekplan.core import IWeekPlanEventProvider
from weekplan.model import WeekPlanEvent


class TimeTrackingWeekPlanEventProvider(Component):
    """Provides events from time tracking logs for the WeekPlan plugin."""
    
    implements(IWeekPlanEventProvider)
    
    def get_plan_prefixes(self):
        return ['log:']
    
    def get_events(self, plan_ids, range):
        prefix = 'log:'
        users = [id[len(prefix):] for id in plan_ids
                                  if id.startswith(prefix)]

        entries = LogEntry.select_by_users_and_date(self.env, users, range[0], range[1])
        tasks = Task.select_by_ids(self.env, [entry.task_id for entry in entries])

        for entry in entries:
            task = tasks[entry.task_id]
            summary_wiki = u'**{0}: {1}: {2}** //({3}h)//'.format(task.category, task.project, task.name, entry.spent_hours)
            if entry.comment:
                summary_wiki += u'\n\n' + entry.comment
            yield WeekPlanEvent(
                prefix + str(entry.id),
                prefix + entry.user,
                summary_wiki,
                entry.date, entry.date)
