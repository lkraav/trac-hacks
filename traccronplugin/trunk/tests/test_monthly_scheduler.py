# -*- coding: utf-8 -*-
from time import localtime, strptime, time

import pytest
from utils import compat_attrgetter

time_now = time()
local_now = localtime(time_now)
local_now_plus_1min = localtime(time_now + 60)
local_now_plus_1hour = localtime(time_now + 3600)
local_now_plus_1day = localtime(time_now + 86400)
local_now_plus_7day = localtime(time_now + 604800)
local_now_plus_1mon = strptime(
    '%s-%s-%s %s:%s:%s' % (local_now.tm_year, local_now.tm_mon + 1,
                           local_now.tm_mday, local_now.tm_hour,
                           local_now.tm_min, local_now.tm_sec),
    '%Y-%m-%d %H:%M:%S')

_getter = compat_attrgetter('tm_mday', 'tm_hour', 'tm_min')
sch_value_now = '%s@%sh%s' % _getter(local_now)
sch_value_now_plus_1min = '%s@%sh%s' % _getter(local_now_plus_1min)
sch_value_now_plus_1hour = '%s@%sh%s' % _getter(local_now_plus_1hour)
sch_value_now_plus_1day = '%s@%sh%s' % _getter(local_now_plus_1day)
sch_value_now_plus_7day = '%s@%sh%s' % _getter(local_now_plus_7day)
sch_value_now_plus_1mon = '%s@%sh%s' % _getter(local_now_plus_1mon)


def pytest_funcarg__monthly_scheduler(request, component):
    monthly_scheduler = component['monthly_scheduler']
    return monthly_scheduler


def test_monthly_scheduler_basic(monthly_scheduler):
    assert 'monthly' == monthly_scheduler.getId()


@pytest.mark.parametrize(('cur_time', 'sch_value', 'expected'), [
    (local_now, sch_value_now, True),
    (local_now, sch_value_now_plus_1min, False),
    (local_now, sch_value_now_plus_1hour, False),
    (local_now, sch_value_now_plus_1day, False),
    (local_now, sch_value_now_plus_7day, False),
    (local_now, sch_value_now_plus_1mon, True),
    (local_now, None, False),
    (local_now, '', False),
])
def test_monthly_scheduler_compareTime(monthly_scheduler,
                                      cur_time, sch_value, expected):
    assert expected is monthly_scheduler.compareTime(cur_time, sch_value)
