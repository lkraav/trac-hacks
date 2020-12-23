# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

import pytest
from utils import create_milestone_ticket, get_or_create_milestone
from utils import has_log_message

from trac.util.datefmt import utc


def pytest_funcarg__auto_postpone_task(request, component):
    auto_postpone_task = component['auto_postpone_task']
    return auto_postpone_task


def test_auto_postpone_task_getId(auto_postpone_task):
    assert 'auto_postpone' == auto_postpone_task.getId()


def test_auto_postpone_task_wake_up_no_milestone(auto_postpone_task, caplog):
    env = auto_postpone_task.env
    caplog.setLevel(logging.DEBUG, logger=env.log.name)

    # create milestone
    m1 = get_or_create_milestone(env)
    auto_postpone_task.wake_up()
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'action controllers for ticket workflow',
        'Creating new milestone',
        'No opened milestone found. Cannot postpone tickets',
    ]
    assert has_log_message(caplog, expected_messages)


def test_auto_postpone_task_wake_up(auto_postpone_task, caplog):
    env = auto_postpone_task.env
    caplog.setLevel(logging.DEBUG, logger=env.log.name)

    # create milestone & ticket
    m1, t1 = create_milestone_ticket(env, 'ms1', 0, 'owner1', 'reporter1')
    t1['status'] = 'new'
    t1.save_changes()
    m1.completed = datetime.now(utc)
    m1.update()

    duedate_plus_5days = datetime.now(utc) + timedelta(days=5)
    m2 = get_or_create_milestone(env, 'ms2', duedate_plus_5days)
    auto_postpone_task.wake_up()
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'action controllers for ticket workflow',
        'Creating new milestone',
        'Updating milestone',
        'Ticket',
    ]
    assert has_log_message(caplog, expected_messages)
