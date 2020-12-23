# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

import pytest
from utils import create_milestone_ticket
from utils import has_log_message

from trac.util.datefmt import utc


def pytest_funcarg__unreachable_milestone_task(request, component):
    unreachable_milestone_task = component['unreachable_milestone_task']
    return unreachable_milestone_task


def test_unreachable_milestone_task_getId(unreachable_milestone_task):
    from traccron.core import CronConfig
    task = unreachable_milestone_task
    assert CronConfig.UNREACHABLE_MILESTONE_TASK_BASEKEY == task.getId()


def test_unreachable_milestone_task_wake_up(unreachable_milestone_task,
                                            caplog):
    env = unreachable_milestone_task.env
    caplog.setLevel(logging.DEBUG, logger=env.log.name)

    # TODO: should be more simple
    # create tickets
    duedate = datetime.now(utc)
    duedate_plus_5days = duedate + timedelta(days=5)
    create_milestone_ticket(env, 'ms1', duedate, 'owner1', 'repo1')
    create_milestone_ticket(env, 'ms1', duedate, 'owner1', 'repo1'),
    create_milestone_ticket(env, 'ms1', duedate, 'owner2', 'repo2'),
    create_milestone_ticket(env, 'ms2', duedate_plus_5days, 'owner1', 'repo1')
    create_milestone_ticket(env, 'ms3', duedate, 'owner1', 'repo1')

    unreachable_milestone_task.wake_up()
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'action controllers for ticket workflow',
        "Creating new milestone 'ms1'",
        "Creating new milestone 'ms2'",
        "Creating new milestone 'ms3'",
        'warning ticket 1 will probably miss its milestone ms1',
        'warning ticket 2 will probably miss its milestone ms1',
        'warning ticket 3 will probably miss its milestone ms1',
        'warning ticket 5 will probably miss its milestone ms3',
        'notify unreachable milestone: ms3, UnreachableMilestoneNotification',
        'notify unreachable milestone: ms1, UnreachableMilestoneNotification',
        'notify opened ticket: owner1, ms3, OwnerOpenedTicketNotification',
        'notify opened ticket: owner1, ms1, OwnerOpenedTicketNotification',
        'notify opened ticket: owner2, ms1, OwnerOpenedTicketNotification',
        'notify opened ticket: repo1, ms3, ReporterOpenedTicketNotification',
        'notify opened ticket: repo1, ms1, ReporterOpenedTicketNotification',
        'notify opened ticket: repo2, ms1, ReporterOpenedTicketNotification',
    ]
    assert has_log_message(caplog, expected_messages)


@pytest.mark.parametrize(('args', 'add_days'), [
    ((), 5),
    ((), 2),
    ((2,), 0),
    ((7, 'test'), 5),
    ((7, 'test'), 10),
])
def test_unreachable_milestone_task_wake_up_args(unreachable_milestone_task,
                                                 caplog, args, add_days):

    from traccron.task import UnreachableMilestoneTask
    env = unreachable_milestone_task.env
    caplog.setLevel(logging.DEBUG, logger=env.log.name)

    # create tickets
    duedate = datetime.now(utc) + timedelta(days=add_days)
    create_milestone_ticket(env, 'ms1', duedate, 'owner1', 'repo1')

    unreachable_milestone_task.wake_up(*args)
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'action controllers for ticket workflow',
        'Creating new milestone',
    ]

    if not args:
        args = (UnreachableMilestoneTask.ahead_days,)

    if add_days <= args[0]:
        expected_messages.extend([
            'warning ticket',
            'notify unreachable milestone',
            'notify opened ticket',
        ])
    assert has_log_message(caplog, expected_messages)
