# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

import pytest
from utils import has_log_message

now = datetime.now()
after_1days = now + timedelta(days=1)
after_3days = now + timedelta(days=3)


def pytest_funcarg__ticket_deadline_task(request, component):
    ticket_deadline_task = component['ticket_deadline_task']
    return ticket_deadline_task


def test_ticket_deadline_task_getId(ticket_deadline_task):
    assert 'ticket_deadline' == ticket_deadline_task.getId()


def _create_tickets(env, date_field_name, date_field):
    from utils import update_value, create_ticket
    env.config.set('ticket-custom', date_field_name, 'text')

    @update_value(date_field_name, date_field)
    @update_value('status', 'new')
    def create_new_ticket_with_duedate(env, **kwargs):
        return create_ticket(env, **kwargs)

    @update_value(date_field_name, date_field)
    @update_value('status', 'closed')
    def create_closed_ticket_with_duedate(env, **kwargs):
        return create_ticket(env, **kwargs)

    t1 = create_new_ticket_with_duedate(env)
    t2 = create_closed_ticket_with_duedate(env)
    return t1, t2


@pytest.mark.parametrize(('args', 'due_date_value', 'is_remind'), [
    (('my_due_date', '%Y/%m/%d', '3'), after_1days.strftime('%Y/%m/%d'), True),
    (('deadline', '%Y-%m-%d', '3'), after_1days.strftime('%Y-%m-%d'), True),
    (('deadline', '%Y-%m-%d', '1'), after_3days.strftime('%Y-%m-%d'), False),
])
def test_ticket_deadline_task_wake_up(ticket_deadline_task, caplog,
                                      args, due_date_value, is_remind):
    env = ticket_deadline_task.env
    caplog.setLevel(logging.DEBUG, logger=env.log.name)

    _create_tickets(env, args[0], due_date_value)
    ticket_deadline_task.wake_up(*args)
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'action controllers for ticket workflow',
        'wake_up',
        'need_notify',
    ]

    if is_remind:
        expected_messages.extend([
            'remind: 1',  # depends on _create_tickets()
        ])
    assert has_log_message(caplog, expected_messages)
