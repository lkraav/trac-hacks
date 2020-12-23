# -*- encoding: UTF-8 -*-
"""
Created on 28 oct. 2010

@author: thierry
"""
###############################################################################
##
##          O U T    O F    T H E    B O X    S C H E D U L E R
##
###############################################################################

import re

from trac.core import Component, implements
from traccron.api import ISchedulerType
from traccron.core import CronConfig


class SchedulerType(ISchedulerType):
    """
    Define a sort of scheduling. Base class for any scheduler type
    implementation
    """
    implements(ISchedulerType)

    def __init__(self):
        self.cronconf = CronConfig(self.env)

    def getId(self):
        """
        Return the id to use in trac.ini for this schedule type
        """
        raise NotImplementedError

    def getHint(self):
        """
        Return a description of what it is and the format used to defined
        the schedule
        """
        return ''

    def isTriggerTime(self, task, currentTime):
        """
        Test is accordingly to this scheduler and given currentTime,
        is time to fire the task
        """
        # read the configuration value for the task
        self.env.log.debug('looking for schedule of type: %s' % self.getId())
        for schedule_value in self._get_task_schedule_value_list(task):
            msg = 'task is scheduled: %s, %s' % (task.getId(), schedule_value)
            self.env.log.debug(msg)
            if self.compareTime(currentTime, schedule_value):
                return True
        self.env.log.debug('no matching schedule found')
        return False

    def compareTime(self, currentTime, schedule_value):
        """
        Test is accordingly to this scheduler, given currentTime and
        schedule value, is time to fire the task.
        currentTime is a structure computed by time.localtime(time())
        scheduled_value is the value of the configuration in trac.ini
        """
        raise NotImplementedError

    def _get_task_schedule_value_list(self, task):
        return self.cronconf.get_schedule_value_list(task, self)

    def _output_comp_debug_log(self, currentTime, schedule_value):
        self.env.log.debug('compareTime: %s, %s, %s' % (
                           self.getId(), currentTime, schedule_value))


class DailyScheduler(Component, SchedulerType):
    """
    Scheduler that trigger a task once a day based uppon a defined time
    """

    def __init__(self):
        SchedulerType.__init__(self)

    def getId(self):
        return 'daily'

    def getHint(self):
        return 'ex: 8h30 fire every day at 8h30'

    def compareTime(self, currentTime, schedule_value):
        self._output_comp_debug_log(currentTime, schedule_value)
        return schedule_value == '%sh%s' % currentTime[3:5]


class HourlyScheduler(Component, SchedulerType):
    """
    Scheduler that trigger a task once an hour at a defined time
    """

    def __init__(self):
        SchedulerType.__init__(self)

    def getId(self):
        return 'hourly'

    def getHint(self):
        return 'ex: 45 fire every hour at 0h45 then 1h45 and so on'

    def compareTime(self, currentTime, schedule_value):
        self._output_comp_debug_log(currentTime, schedule_value)
        return schedule_value == str(currentTime.tm_min)


class WeeklyScheduler(Component, SchedulerType):
    """
    Scheduler that trigger a task once a week at a defined day and time
    """

    def __init__(self):
        SchedulerType.__init__(self)

    def getId(self):
        return 'weekly'

    def getHint(self):
        return 'ex: 0@12h00 fire every monday at 12h00'

    def compareTime(self, currentTime, schedule_value):
        self._output_comp_debug_log(currentTime, schedule_value)
        return schedule_value == '%s@%sh%s' % (currentTime.tm_wday,
                                               currentTime.tm_hour,
                                               currentTime.tm_min)


class MonthlyScheduler(Component, SchedulerType):
    """
    Scheduler that trigger a task once a week at a defined day and time
    """

    def __init__(self):
        SchedulerType.__init__(self)

    def getId(self):
        return 'monthly'

    def getHint(self):
        msg = 'ex: 15@12h00 fire every month on the 15th day of month at 12h00'
        return msg

    def compareTime(self, currentTime, schedule_value):
        self._output_comp_debug_log(currentTime, schedule_value)
        return schedule_value == '%s@%sh%s' % (currentTime.tm_mday,
                                               currentTime.tm_hour,
                                               currentTime.tm_min)


class CronScheduler(Component, SchedulerType):
    """
    Scheduler that used a cron-like syntax to specified when task must
    be triggered. Use cron like expression,
    set either day-of-month or day-of-week and other one must be '?'

    ex: *  *  *  ?  *  ?  *
        ┬  ┬  ┬  ┬  ┬  ┬  ┬
        │  │  │  │  │  │  └--── year (omissible)
        │  │  │  │  │  └─────── day of week (1 - 7, 1 is Monday)
        │  │  │  │  └────────── month (1 - 12)
        │  │  │  └───────────── day of month (1 - 31)
        │  │  └──────────────── hour (0 - 23)
        │  └─────────────────── min (0 - 59)
        └────────────────────── None (reserved?)
    """
    cron_syntax = re.compile(r"""
        (?P<value>
            \* |
            (?P<pre>\d+)(?P<sep>[-|\/])(?P<post>\d+) |  # e.g.) 1-31, 0/2
            \d+
        )""", re.X)

    class AllMatch(set):
        """
        Universal set - match everything
        Stand for * in cron expression
        """
        def __contains__(self, item):
            return True

    class OmitMatch(AllMatch):
        """
        Stand for ? in cron expression
        """
        pass

    class CronExpressionError(Exception):
        pass

    _allMatch = AllMatch()
    _omitMatch = OmitMatch()

    # The actual Event class
    class Event(object):
        def __init__(self, min, hour, day, month, dow, year):
            self.mins = self.conv_to_set(min)
            self.hours = self.conv_to_set(hour)
            self.days = self.conv_to_set(day)
            self.months = self.conv_to_set(month)
            self.dow = self.conv_to_set(dow)
            self.year = self.conv_to_set(year)

        def conv_to_set(self, obj):  # Allow single integer to be provided
            if isinstance(obj, (int, long)):
                return set([obj])  # Single item
            elif not isinstance(obj, set):
                return set(obj)
            else:
                return obj

        def matchtime(self, t):
            """
            Return True if this event should trigger at the specified localtime
            """
            return ((t.tm_min in self.mins) and
                    (t.tm_hour in self.hours) and
                    (t.tm_mday in self.days) and
                    (t.tm_mon in self.months) and
                    (t.tm_wday in self.dow) and
                    (t.tm_year in self.year))

    def __init__(self):
        SchedulerType.__init__(self)

    def getId(self):
        return 'cron'

    def getHint(self):
        return 'ex: * 5 10 * * ? * fire every day at 10h5'

    def compareTime(self, currentTime, schedule_value):
        self._output_comp_debug_log(currentTime, schedule_value)
        try:
            cron_settings = self._parse_cron_expression(schedule_value)
        except CronScheduler.CronExpressionError:
            self.env.log.debug('Failed to parse cron expression')
            return False
        else:
            return CronScheduler.Event(**cron_settings).matchtime(currentTime)

    def _output_range_error(self, value, name, min_value, max_value):
        msg = 'invalid cron expression: %s is out of range [%d-%d] for %s'
        self.env.log.error(msg % (value, min_value, max_value, name))

    def _get_cron_value_range(self, field, name, min_value, max_value, adjust):
        _begin = int(field.get('pre'))
        _end = int(field.get('post'))
        if _begin < min_value:
            self._output_range_error(_begin, name, min_value, max_value)
            raise CronScheduler.CronExpressionError()
        elif _end > max_value:
            self._output_range_error(_end, name, min_value, max_value)
            raise CronScheduler.CronExpressionError()
        # cron range expression is inclusive
        return range(_begin + adjust, _end + 1 + adjust)

    def _get_cron_value_every(self, field, name, min_value, max_value, adjust):
        _begin = int(field.get('pre'))
        if ((_begin < min_value) or (_begin > max_value)):
            self._output_range_error(_begin, name, min_value, max_value)
            raise CronScheduler.CronExpressionError()
        _step = int(field.get('post'))
        # cron range expression is inclusive
        return range(_begin + adjust, max_value + 1 + adjust, _step)

    def _get_cron_value_int(self, value, name, min_value, max_value, adjust):
        _value = int(value)
        if (_value < min_value) or (_value > max_value):
            self._output_range_error(value, name, min_value, max_value)
            raise CronScheduler.CronExpressionError()
        return _value + adjust

    def _parse_cron_value(self, name, value, min_value, max_value, adjust=0):
        """
        utility method to parse value of a cron item.
        Support of *, range expression (ex 1-10)
        adjust is used to translate value
        (ex: first day of week is 0 in python and 1 in Cron)
        """
        match = re.match(CronScheduler.cron_syntax, value)
        if not match:
            self.env.log.error('invalid cron expression: ')
            raise CronScheduler.CronExpressionError()

        cron_field = match.groupdict()
        cron_value = cron_field.get('value')
        cron_sep = cron_field.get('sep')
        if cron_value == '*':
            return CronScheduler._allMatch
        elif cron_sep == '-':
            return self._get_cron_value_range(cron_field, name,
                                              min_value, max_value, adjust)
        elif cron_sep == '/':
            return self._get_cron_value_every(cron_field, name,
                                              min_value, max_value, adjust)
        else:
            return self._get_cron_value_int(cron_value, name,
                                            min_value, max_value, adjust)

    def _parse_cron_day_fields(self, day_of_month, day_of_week):
        if (day_of_month == '?' and day_of_week == '?') or \
           (day_of_month != '?' and day_of_week != '?'):
            self.env.log.error('invalid cron expression: set value '
                               'either day-of-month or day-of-week')
            raise CronScheduler.CronExpressionError()

        if day_of_month != '?':
            day_value = self._parse_cron_value('day', day_of_month, 1, 31)
            dow_value = CronScheduler._omitMatch
        elif day_of_week != '?':
            day_value = CronScheduler._omitMatch
            dow_value = self._parse_cron_value('day-of-week', day_of_week,
                                               1, 7, adjust=-1)
        return day_value, dow_value

    def _parse_cron_expression(self, cron_text):
        """
        Parse cron expression and return dictionary of argument key/value
        suitable for Event object
        """
        self.env.log.debug('parsing cron expression: "%s"' % cron_text)
        if not cron_text:
            raise CronScheduler.CronExpressionError()

        cron_params = cron_text.split()[0:7]
        cron_params_length = len(cron_params)

        if cron_params_length < 6:
            self.env.log.error('cron expression must have at least 6 items')
            raise CronScheduler.CronExpressionError()
        elif cron_params_length == 6:
            cron_params.append('*')  # year field can be abbreviate

        day_dow = cron_params[3], cron_params[5]
        day_value, dow_value = self._parse_cron_day_fields(*day_dow)
        cron_settings = {
            'min': self._parse_cron_value('min', cron_params[1], 0, 59),
            'hour': self._parse_cron_value('hour', cron_params[2], 0, 23),
            'day': day_value,
            'month': self._parse_cron_value('month', cron_params[4], 1, 12),
            'dow': dow_value,
            'year': self._parse_cron_value('year', cron_params[6], 1970, 2099)
        }
        self.env.log.debug('result of parsing is %s' % cron_settings)
        return cron_settings
