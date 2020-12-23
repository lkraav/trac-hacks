# -*- coding: utf-8 -*-
from time import localtime, time

import pytest

time_now = time()
local_now = localtime(time_now)
local_now_plus_1min = localtime(time_now + 60)
local_now_plus_1hour = localtime(time_now + 3600)


def pytest_funcarg__hourly_scheduler(request, component):
    hourly_scheduler = component['hourly_scheduler']
    return hourly_scheduler


def test_hourly_scheduler_basic(hourly_scheduler):
    assert 'hourly' == hourly_scheduler.getId()


@pytest.mark.parametrize(('cur_time', 'sch_value', 'expected'), [
    (local_now, '%s' % local_now[4], True),
    (local_now, '%s' % local_now_plus_1min[4], False),
    (local_now, '%s' % local_now_plus_1hour[4], True),
    (local_now, None, False),
    (local_now, '', False),
])
def test_hourly_scheduler_compareTime(hourly_scheduler,
                                      cur_time, sch_value, expected):
    assert expected is hourly_scheduler.compareTime(cur_time, sch_value)
