import urllib
import datetime

from icalendar import Calendar
import recurring_ical_events

from trac.config import ConfigSection
from trac.core import Component, implements
from trac.util.datefmt import format_time, user_time
from weekplan.core import IWeekPlanEventProvider
from weekplan.model import WeekPlanEvent


class ICalWeekPlanEventProvider(Component):
    """Provides events from ical feeds like Google Calendar."""

    implements(IWeekPlanEventProvider)

    ical_section = ConfigSection('week-plan-ical-feeds',
        """Every option in the `[week-plan-ical-feeds]` section defines one ical
        feed. The option name defines the plan name. The option value defines
        the URL.

        '''Example:'''
        {{{
        [week-plan-ical-feeds]
        trac = https://trac.edgewall.org/roadmap?format=ics
        }}}
        """)

    def get_plan_prefixes(self):
        return ['ical:']

    def get_events(self, req, plan_ids, range):
        def get_ical_entries(ical_url):
            f = urllib.urlopen(ical_url)
            content = f.read()
            calendar = Calendar.from_ical(content)
            entries = calendar.walk()
            if range is not None:
                r0, r1 = range
                recurring_events = recurring_ical_events.of(calendar).between(r0, r1)
                entries.extend(recurring_events)
            return entries

        def is_relevant(entry):
            if entry.name != "VEVENT":
                return False
            start = entry.get('dtstart')
            end = entry.get('dtend')
            if start is None:
                return False
            if end is None:
                end = start
            if range is not None:
                r0, r1 = range
                if not isinstance(start.dt, datetime.datetime):
                    r1 = r1.date()
                if not isinstance(end.dt, datetime.datetime):
                    r0 = r0.date()
                if end.dt < r0 or r1 < start.dt:
                    return False
            return True

        def ical_entry_to_week_plan_event(entry, plan):
            entry_id = entry.get('UID')
            start = entry.get('dtstart')
            end = entry.get('dtend')
            summary = entry.get('summary')
            description = entry.get('description')
            if end is None:
                end = start
            title = str(summary)
            if description:
                title += ' ' + str(description)
            if isinstance(start.dt, datetime.datetime):
                title = user_time(req, format_time, start.dt) + ' ' + title
            start = start.dt
            end = end.dt
            if isinstance(start, datetime.date):
                start = datetime.datetime.combine(start, datetime.time(12, 0))
            if isinstance(end, datetime.date):
                end = datetime.datetime.combine(end, datetime.time(12, 0))
            return WeekPlanEvent(str(entry_id), plan, title, start, end)

        events = []
        for plan_suffix, ical_url in self.ical_section.options():
            plan_id = 'ical:' + plan_suffix
            if plan_ids and plan_id not in plan_ids:
                continue
            for entry in get_ical_entries(ical_url):
                try:
                    if is_relevant(entry):
                        event = ical_entry_to_week_plan_event(entry, plan_id)
                        events.append(event)
                except BaseException as e:
                    self.log.error("Error accessing week-plan '%s': %s", plan_id, e)
        return events
