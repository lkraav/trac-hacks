# -*- coding: utf-8 -*-
from time import localtime, time

import pytest
from utils import compat_attrgetter

time_now = time()
local_now = localtime(time_now)
local_now_plus_1min = localtime(time_now + 60)
local_now_plus_1hour = localtime(time_now + 3600)
local_now_plus_1day = localtime(time_now + 86400)
local_now_plus_7day = localtime(time_now + 604800)

_getter = compat_attrgetter('tm_wday', 'tm_hour', 'tm_min')
sch_value_now = '%s@%sh%s' % _getter(local_now)
sch_value_now_plus_1min = '%s@%sh%s' % _getter(local_now_plus_1min)
sch_value_now_plus_1hour = '%s@%sh%s' % _getter(local_now_plus_1hour)
sch_value_now_plus_1day = '%s@%sh%s' % _getter(local_now_plus_1day)
sch_value_now_plus_7day = '%s@%sh%s' % _getter(local_now_plus_7day)


def pytest_funcarg__weekly_scheduler(request, component):
    weekly_scheduler = component['weekly_scheduler']
    return weekly_scheduler


def test_weekly_scheduler_basic(weekly_scheduler):
    assert 'weekly' == weekly_scheduler.getId()


@pytest.mark.parametrize(('cur_time', 'sch_value', 'expected'), [
    (local_now, sch_value_now, True),
    (local_now, sch_value_now_plus_1min, False),
    (local_now, sch_value_now_plus_1hour, False),
    (local_now, sch_value_now_plus_1day, False),
    (local_now, sch_value_now_plus_7day, True),
    (local_now, None, False),
    (local_now, '', False),
])
def test_weekly_scheduler_compareTime(weekly_scheduler,
                                      cur_time, sch_value, expected):
    assert expected is weekly_scheduler.compareTime(cur_time, sch_value)
