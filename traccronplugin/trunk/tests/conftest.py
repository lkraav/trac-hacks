# -*- coding: utf-8 -*-
from trac.test import EnvironmentStub

from traccron.core import Core as CronCore
from traccron.history import MemoryHistoryStore
from traccron.listener import HistoryTaskEvent
from traccron.listener import NotificationEmailTaskEvent
from traccron.scheduler import CronScheduler
from traccron.scheduler import DailyScheduler
from traccron.scheduler import HourlyScheduler
from traccron.scheduler import MonthlyScheduler
from traccron.scheduler import WeeklyScheduler
from traccron.task import AutoPostponeTask
from traccron.task import HeartBeatTask
from traccron.task import SleepingTicketReminderTask
from traccron.task import UnreachableMilestoneTask
from traccron.task import TicketDeadlineTask


def pytest_addoption(parser):
    group = parser.getgroup('general')
    group.addoption('--envscope',
                    action='store', dest='envscope', default='function',
                    type='choice', choices=['module', 'function'],
                    help=('set environment scope, default: module.'))

def make_trac_environment_with_plugin():
    env = EnvironmentStub(enable=['traccron.*'])

    # replace default logger name with own testing name since
    # the log handler settings is defferent from trac-0.12 and 1.0
    import logging
    env.log = logging.getLogger('traccron-test')
    env.log.addHandler(env._log_handler)

    component = {
        'core': CronCore(env),
        'memory_history_store': MemoryHistoryStore(env),
        'history_task_event': HistoryTaskEvent(env),
        'notification_email_task_event': NotificationEmailTaskEvent(env),
        'cron_scheduler': CronScheduler(env),
        'daily_scheduler': DailyScheduler(env),
        'hourly_scheduler': HourlyScheduler(env),
        'monthly_scheduler': MonthlyScheduler(env),
        'weekly_scheduler': WeeklyScheduler(env),
        'auto_postpone_task': AutoPostponeTask(env),
        'heart_beat_task': HeartBeatTask(env),
        'sleeping_ticket_reminder_task': SleepingTicketReminderTask(env),
        'unreachable_milestone_task': UnreachableMilestoneTask(env),
        'ticket_deadline_task': TicketDeadlineTask(env),
    }
    return env, component

def pytest_funcarg__env(request):
    setup = make_trac_environment_with_plugin
    scope = request.config.option.envscope
    env, component = request.cached_setup(setup=setup, scope=scope)
    return env

def pytest_funcarg__component(request):
    setup = make_trac_environment_with_plugin
    scope = request.config.option.envscope
    env, component = request.cached_setup(setup=setup, scope=scope)
    return component
