# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

import pytest
from utils import create_orphaned_ticket, create_new_tickets
from utils import has_log_message

from trac.util.datefmt import utc


def pytest_funcarg__sleeping_ticket_reminder_task(request, component):
    sleeping_ticket_reminder_task = component['sleeping_ticket_reminder_task']
    return sleeping_ticket_reminder_task


def test_sleeping_ticket_reminder_task_getId(sleeping_ticket_reminder_task):
    assert 'sleeping_ticket' == sleeping_ticket_reminder_task.getId()


@pytest.mark.parametrize(('args', 'subtract_days'), [
    ((), 5),
    ((), 2),
    ((2,), 5),
    ((7, 'test'), 5),
    ((7, 'test'), 10),
])
def test_sleeping_ticket_reminder_task_wake_up(sleeping_ticket_reminder_task,
                                               caplog, args, subtract_days):
    from traccron.task import SleepingTicketReminderTask
    env = sleeping_ticket_reminder_task.env
    caplog.setLevel(logging.DEBUG, logger=env.log.name)

    # create tickets
    when = datetime.now(utc) - timedelta(days=subtract_days)
    t1 = create_new_tickets(env, 3, owner='sleeper1', when=when)
    o1 = create_orphaned_ticket(env, when=when)

    sleeping_ticket_reminder_task.wake_up(*args)
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'action controllers for ticket workflow',
    ]

    if not args:
        args = (SleepingTicketReminderTask.delay_days,)

    if args[0] <= subtract_days:
        expected_messages.extend([
            'warning sleeping ticket',
            'warning ticket',
        ])
    assert has_log_message(caplog, expected_messages)
