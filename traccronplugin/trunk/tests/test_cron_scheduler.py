# -*- coding: utf-8 -*-
from time import localtime, time

import pytest
from utils import compat_attrgetter

time_now = time()
local_now = localtime(time_now)
local_now_plus_1hour = localtime(time_now + 3600)

_getter_all = compat_attrgetter('tm_min', 'tm_hour', 'tm_mday',
                                'tm_mon', 'tm_wday', 'tm_year')
_getter_mday = compat_attrgetter('tm_min', 'tm_hour', 'tm_mday',
                                 'tm_mon', 'tm_year')

sch_value_invalid_all = '* %s %s %s %s %s %s' % _getter_all(local_now)
sch_value_now_mday = '* %s %s %s %s ? %s' % _getter_mday(local_now)
sch_value_now_wday = '* %s %s ? %s %s %s' % (local_now.tm_min,
                                             local_now.tm_hour,
                                             local_now.tm_mon,
                                             local_now.tm_wday + 1,
                                             local_now.tm_year)
sch_value_every_min = '* 0/1 * * * ? *'
sch_value_every_hour = '* %s 0/1 * * ? *' % local_now.tm_min
sch_value_range_mday = '* %s %s 1-31 * ? *' % (local_now.tm_min,
                                               local_now.tm_hour)
sch_value_range_wday = '* %s %s ? * 1-7 *' % (local_now.tm_min,
                                              local_now.tm_hour)
sch_value_now_plus_1hour = '* %s %s %s %s ? %s' % (_getter_mday(
                                                   local_now_plus_1hour))
sch_value_no_year = '* %s %s * * ?' % (local_now.tm_min, local_now.tm_hour)

# error cron sentences
sch_value_out_of_min = '* 80/5 * * * ? *'
sch_value_out_of_hour = '* 1 20-25 * * ? *'
sch_value_out_of_mday = '* 2 7 32 * ? *'
sch_value_out_of_month = '* 3 8 ? 13 1 *'
sch_value_out_of_wday = '* 4 9 ? * 0 *'


def pytest_funcarg__cron_scheduler(request, component):
    cron_scheduler = component['cron_scheduler']
    return cron_scheduler


def test_cron_scheduler_basic(cron_scheduler):
    assert 'cron' == cron_scheduler.getId()


@pytest.mark.parametrize(('cur_time', 'sch_value', 'expected'), [
    (local_now, sch_value_invalid_all, False),
    (local_now, sch_value_now_mday, True),
    (local_now, sch_value_now_wday, True),
    (local_now, sch_value_every_min, True),
    (local_now, sch_value_every_hour, True),
    (local_now, sch_value_range_mday, True),
    (local_now, sch_value_range_wday, True),
    (local_now, sch_value_now_plus_1hour, False),
    (local_now, sch_value_no_year, True),
    (local_now, None, False),
    (local_now, sch_value_out_of_min, False),
    (local_now, sch_value_out_of_hour, False),
    (local_now, sch_value_out_of_mday, False),
    (local_now, sch_value_out_of_month, False),
    (local_now, sch_value_out_of_wday, False),
    (local_now, '', False),
])
def test_cron_scheduler_compareTime(cron_scheduler,
                                    cur_time, sch_value, expected):
    assert expected is cron_scheduler.compareTime(cur_time, sch_value)
