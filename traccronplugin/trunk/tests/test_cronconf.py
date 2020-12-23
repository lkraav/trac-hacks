# -*- encoding: UTF-8 -*-
import pytest

from traccron.core import CronConfig


def pytest_funcarg__cronconf(request, env):
    cronconf = CronConfig(env)
    return cronconf

def pytest_funcarg__task(request, component):
    task = component['heart_beat_task']
    return task

def pytest_funcarg__cron_scheduler(request, component):
    cron_scheduler = component['cron_scheduler']
    return cron_scheduler

def pytest_funcarg__history_task_event(request, component):
    history_task_event = component['history_task_event']
    return history_task_event


def test_get_ticker_enabled(cronconf):
    default_value = eval(CronConfig.TICKER_ENABLED_DEFAULT)
    assert default_value is cronconf.get_ticker_enabled()

def test_set_ticker_enabled(cronconf):
    cronconf.set_ticker_enabled(True)
    assert True is cronconf.get_ticker_enabled()
    cronconf.set_ticker_enabled(False)
    assert False is cronconf.get_ticker_enabled()

def test_get_ticker_interval(cronconf):
    assert CronConfig.TICKER_INTERVAL_DEFAULT == cronconf.get_ticker_interval()

def test_set_ticker_interval(cronconf):
    cronconf.set_ticker_interval(10)
    assert 10 == cronconf.get_ticker_interval()


def test_get_schedule_value(cronconf, task, cron_scheduler):
    assert None is cronconf.get_schedule_value(task, cron_scheduler)

def test_get_schedule_value_list(cronconf, task, cron_scheduler):
    assert 0 == len(cronconf.get_schedule_value_list(task, cron_scheduler))

def test_set_schedule_value(cronconf, task, cron_scheduler):
    value = '*/1 * * * * *'
    cronconf.set_schedule_value(task, cron_scheduler, value)
    assert value == cronconf.get_schedule_value(task, cron_scheduler)
    assert 1 == len(cronconf.get_schedule_value_list(task, cron_scheduler))


def test_is_task_enabled(cronconf, task):
    default_value = eval(CronConfig.TASK_ENABLED_DEFAULT)
    assert default_value is cronconf.is_task_enabled(task)

def test_set_task_enabled(cronconf, task):
    cronconf.set_task_enabled(task, True)
    assert True is cronconf.is_task_enabled(task)
    cronconf.set_task_enabled(task, False)
    assert False is cronconf.is_task_enabled(task)


def test_is_schedule_enabled(cronconf, task, cron_scheduler):
    default_value = eval(CronConfig.SCHEDULE_ENABLED_DEFAULT)
    assert default_value is cronconf.is_schedule_enabled(task, cron_scheduler)

def test_set_schedule_enabled(cronconf, task, cron_scheduler):
    cronconf.set_schedule_enabled(task, cron_scheduler, True)
    assert True is cronconf.is_schedule_enabled(task, cron_scheduler)
    cronconf.set_schedule_enabled(task, cron_scheduler, False)
    assert False is cronconf.is_schedule_enabled(task, cron_scheduler)


def test_get_schedule_arg(cronconf, task, cron_scheduler):
    assert None is cronconf.get_schedule_arg(task, cron_scheduler)

def test_get_schedule_arg_list(cronconf, task, cron_scheduler):
    assert 0 == len(cronconf.get_schedule_arg_list(task, cron_scheduler))

def test_set_schedule_arg(cronconf, task, cron_scheduler):
    value = 'testtest'
    cronconf.set_schedule_arg(task, cron_scheduler, value)
    assert value == cronconf.get_schedule_arg(task, cron_scheduler)
    assert 1 == len(cronconf.get_schedule_arg_list(task, cron_scheduler))


def test_get_email_notifier_task_limit(cronconf):
    default_value = CronConfig.EMAIL_NOTIFIER_TASK_LIMIT_DEFAULT
    assert default_value == cronconf.get_email_notifier_task_limit()

def test_get_email_notifier_task_recipient(cronconf):
    default_value = CronConfig.EMAIL_NOTIFIER_TASK_RECIPIENT_DEFAULT
    assert default_value == cronconf.get_email_notifier_task_recipient()

def test_get_email_notifier_task_recipient_list(cronconf):
    assert 0 == len(cronconf.get_email_notifier_task_recipient_list())


def test_is_email_notifier_only_error(cronconf):
    default_value = eval(CronConfig.EMAIL_NOTIFIER_TASK_ONLY_ERROR_DEFAULT)
    assert default_value is cronconf.is_email_notifier_only_error()

def test_set_email_notifier_only_error(cronconf):
    cronconf.set_email_notifier_only_error(True)
    assert True is cronconf.is_email_notifier_only_error()
    cronconf.set_email_notifier_only_error(False)
    assert False is cronconf.is_email_notifier_only_error()


def test_is_task_listener_enabled(cronconf, history_task_event):
    def_value = eval(CronConfig.TASK_LISTENER_ENABLED_DEFAULT)
    assert def_value is cronconf.is_task_listener_enabled(history_task_event)

def test_set_task_listener_enabled(cronconf, history_task_event):
    cronconf.set_task_listener_enabled(history_task_event, True)
    assert True is cronconf.is_task_listener_enabled(history_task_event)
    cronconf.set_task_listener_enabled(history_task_event, False)
    assert False is cronconf.is_task_listener_enabled(history_task_event)


def test_get_unreachable_milestone_task_recipient_list(cronconf):
    assert 0 == len(cronconf.get_unreachable_milestone_task_recipient_list())

def test_get_unreachable_milestone_task_recipient(cronconf):
    default_value = CronConfig.UNREACHABLE_MILESTONE_TASK_RECIPIENT_DEFAULT
    assert default_value == cronconf.get_unreachable_milestone_task_recipient()


def test_set_and_remove_value(cronconf):
    section = CronConfig.TRACCRON_SECTION
    key, value = 'cronconf-test', 'cronconf-test-value'
    cronconf.set_value(key, value)
    assert value == cronconf.env.config.get(section, key, None)
    cronconf.remove_value(key)
    assert None is cronconf.env.config.get(section, key, None)
