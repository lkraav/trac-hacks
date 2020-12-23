# -*- coding: utf-8 -*-
from time import localtime, time

import pytest

time_now = time()
local_now = localtime(time_now)
local_now_plus_1min = localtime(time_now + 60)
local_now_plus_1hour = localtime(time_now + 3600)


def pytest_funcarg__daily_scheduler(request, component):
    daily_scheduler = component['daily_scheduler']
    return daily_scheduler


def test_daily_scheduler_basic(daily_scheduler):
    assert 'daily' == daily_scheduler.getId()


@pytest.mark.parametrize(('cur_time', 'sch_value', 'expected'), [
    (local_now, '%sh%s' % local_now[3:5], True),
    (local_now, '%sh%s' % local_now_plus_1min[3:5], False),
    (local_now, '%sh%s' % local_now_plus_1hour[3:5], False),
    (local_now, None, False),
    (local_now, '', False),
])
def test_daily_scheduler_compareTime(daily_scheduler,
                                     cur_time, sch_value, expected):
    assert expected is daily_scheduler.compareTime(cur_time, sch_value)
