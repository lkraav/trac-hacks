# -*- coding: utf-8 -*-
import textwrap

import pytest

from traccron.listener import NotifyEmailTaskEvent


def pytest_funcarg__task(request, component):
    task = component['heart_beat_task']
    return task

def pytest_funcarg__notification_email_task_event(request, component):
    notification_email_task_event = component['notification_email_task_event']
    return notification_email_task_event


def test_notify_email_task_event_basic(env, task):
    from traccron.listener import StartTaskEvent, EndTaskEvent
    # task event settings
    event = NotifyEmailTaskEvent(env)
    key = event.cronconf.email_notifier_task_recipient_key
    event.cronconf.set_value(key, 'admin')

    # notify recipients
    assert ([u'admin'], []) == event.get_recipients(1)

    # notify message body
    start_task_event = StartTaskEvent(task)
    end_task_event = EndTaskEvent(task, True)
    event.notifyTaskEvent([start_task_event, end_task_event])
    msg_tmpl = """\
        task[%s]
        started at %s h %s
        ended at %s h %s
        success\n\n"""
    expected = textwrap.dedent(msg_tmpl % (
        task.getId(),
        start_task_event.time.tm_hour,
        start_task_event.time.tm_min,
        end_task_event.time.tm_hour,
        end_task_event.time.tm_min
    ))
    assert expected == event.data['notify_body']


def test_notification_email_task_event_basic(notification_email_task_event,
                                             task):
    event = notification_email_task_event  # just an alias
    id_ = event.cronconf.EMAIL_NOTIFIER_TASK_BASEKEY
    assert id_ == event.getId()

    # notify recipients settings
    key = event.cronconf.email_notifier_task_recipient_key
    event.cronconf.set_value(key, 'myuser')
    recipients = event.cronconf.get_email_notifier_task_recipient_list()
    assert [u'myuser'] == recipients

    # operate tasks
    event.onStartTask(task)
    assert 1 == event.task_count
    event.onEndTask(task, False)
    assert 0 == event.task_count
    assert 0 == len(event.task_event_buffer)

    # notify message body
    assert isinstance(event.notifier, NotifyEmailTaskEvent)
    notify_body = event.notifier.data.get('notify_body') or ''
    assert notify_body.startswith('task[%s]' % task.getId())
