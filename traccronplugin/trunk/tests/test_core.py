# -*- coding: utf-8 -*-
import logging
import time

import pytest
from utils import has_log_message


def pytest_funcarg__core(request, component):
    core = component['core']
    return core


def test_apply_config_with_disabled_ticker(core, caplog):
    caplog.setLevel(logging.DEBUG, logger=core.env.log.name)
    core.apply_config()  # in case ticker is disabled
    expected_messages = [
        'applying config',
        'ticker is disabled',
    ]
    assert has_log_message(caplog, expected_messages)


def test_apply_config_with_enabled_ticker(core, caplog):
    from traccron.core import Core, Ticker
    caplog.setLevel(logging.DEBUG, logger=core.env.log.name)
    core.getCronConf().set_ticker_enabled(True)
    core.apply_config()  # in case ticker is enabled
    try:
        assert isinstance(Core.current_ticker, Ticker)
        prev_timer_id = id(Core.current_ticker.timer)
        core.apply_config(wait=True)
        assert prev_timer_id != id(Core.current_ticker.timer)
        expected_messages = [
            'applying config',
            'ticker is enabled',
            'ticker is disabled',
            'check existing task',
            'check task:',
            'looking for schedule of type:',
            'no matching schedule found',
            'nothing to do:',
            'create new ticker',
            'new ticker started',
            'stop existing ticker',
            'ticker is enabled',
        ]
        assert has_log_message(caplog, expected_messages)
    finally:
        Core.current_ticker.cancel(wait=True)


def test_getCronConf(core):
    from traccron.core import CronConfig
    cron_conf = core.getCronConf()
    assert isinstance(cron_conf, CronConfig)

    # ticker status
    cron_conf.set_ticker_enabled(True)
    assert True is cron_conf.get_ticker_enabled()
    cron_conf.set_ticker_enabled(False)
    assert False is cron_conf.get_ticker_enabled()

    # ticker interval
    assert 1 == cron_conf.get_ticker_interval()
    cron_conf.set_ticker_interval(60)
    assert 60 == cron_conf.get_ticker_interval()


def test_getTaskList(core):
    from traccron.task import AutoPostponeTask
    from traccron.task import HeartBeatTask
    from traccron.task import SleepingTicketReminderTask
    from traccron.task import UnreachableMilestoneTask
    from traccron.task import TicketDeadlineTask
    task_list = core.getTaskList()
    task_classes = [AutoPostponeTask, HeartBeatTask,
                    SleepingTicketReminderTask, UnreachableMilestoneTask,
                    TicketDeadlineTask]
    assert _isinstances(task_list, task_classes)


def test_getSupportedScheduleType(core):
    from traccron.scheduler import CronScheduler
    from traccron.scheduler import DailyScheduler
    from traccron.scheduler import HourlyScheduler
    from traccron.scheduler import MonthlyScheduler
    from traccron.scheduler import WeeklyScheduler
    schedule_type = core.getSupportedScheduleType()
    schedule_classes = [CronScheduler, DailyScheduler, HourlyScheduler,
                        MonthlyScheduler, WeeklyScheduler]
    assert _isinstances(schedule_type, schedule_classes)


def test_getHistoryList(core):
    from traccron.history import MemoryHistoryStore
    history_list = core.getHistoryList()
    history_classes = [MemoryHistoryStore]
    assert _isinstances(history_list, history_classes)

    # clear history
    core.clearHistory()  # initialize
    try:
        start = time.time()
        end = start + 3600
        for hist in history_list:
            hist.addExecution(object(), start, end, True)
            assert 1 == len(hist.history)
    finally:
        core.clearHistory()
        for hist in history_list:
            assert 0 == len(hist.history)


def test_getTaskListnerList(core):
    from traccron.listener import HistoryTaskEvent
    from traccron.listener import NotificationEmailTaskEvent
    listener_list = core.getTaskListnerList()
    listener_classes = [HistoryTaskEvent, NotificationEmailTaskEvent]
    assert _isinstances(listener_list, listener_classes)


def test_check_task(core, caplog):
    caplog.setLevel(logging.DEBUG, logger=core.env.log.name)
    core.check_task()
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'check existing task',
        'check task:',
        'nothing to do:',
        'looking for schedule of type:',
        'no matching schedule found',
    ]
    assert has_log_message(caplog, expected_messages)


def test_run_task(core, component, caplog):
    caplog.setLevel(logging.DEBUG, logger=core.env.log.name)
    core.runTask(component['heart_beat_task'])
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'executing task: heart_beat',
        'Heart beat: boom boom !!!',
        'task execution result is SUCCESS',
        'notifying task event...',
        'no recipient for task event, aborting',
        'task is finished: heart_beat',
    ]
    assert has_log_message(caplog, expected_messages)


"""
utility functions
"""
def _isinstances(obj_list, classes):
    for obj in obj_list:
        for klass in classes:
            if isinstance(obj, klass):
                break
        else:
            assert False, 'unknown object: %s' % obj
    return True
