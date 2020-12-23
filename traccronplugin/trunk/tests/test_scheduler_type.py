# -*- coding: utf-8 -*-
from time import localtime, time

import pytest

time_now = time()
local_now = localtime(time_now)

def pytest_funcarg__task(request, component):
    task = component['heart_beat_task']
    return task

def pytest_funcarg__my_scheduler(request, env):
    from traccron.scheduler import SchedulerType

    class MyScheduler(SchedulerType):
        def __init__(self, env):
            self.env = env
            self.schedule_task_list = []
            SchedulerType.__init__(self)

        def getId(self):
            return 'myscheduler'

        def compareTime(self, currentTime, schedule_value):
            return currentTime == schedule_value

        def _get_task_schedule_value_list(self, task):
            return self.schedule_task_list

    my_scheduler = MyScheduler(env)
    return my_scheduler


@pytest.mark.parametrize(('cur_time', 'value_list', 'expected'), [
    (local_now, [local_now], True),
    (local_now, ['', local_now], True),
    (local_now, [None, local_now], True),
    (local_now, [], False),
    (local_now, [''], False),
    (local_now, ['9h10'], False),
    (local_now, [None], False),
])
def test_isTriggerTime(my_scheduler, task, cur_time, value_list, expected):
    my_scheduler.schedule_task_list = value_list
    assert expected is my_scheduler.isTriggerTime(task, cur_time)
