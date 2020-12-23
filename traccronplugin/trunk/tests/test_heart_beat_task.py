# -*- coding: utf-8 -*-
import logging

import pytest
from utils import has_log_message


def pytest_funcarg__heart_beat_task(request, component):
    heart_beat_task = component['heart_beat_task']
    return heart_beat_task


def test_heart_beat_task_getId(heart_beat_task):
    assert 'heart_beat' == heart_beat_task.getId()


def test_heart_beat_task_wake_up(heart_beat_task, caplog):
    caplog.setLevel(logging.DEBUG, logger=heart_beat_task.env.log.name)
    heart_beat_task.wake_up()
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'Heart beat: boom boom !!!',
    ]
    assert has_log_message(caplog, expected_messages)


@pytest.mark.parametrize('args', [
    (),
    ('test',),
    ('test', 'data'),
])
def test_heart_beat_task_wake_up_with_args(heart_beat_task, caplog, args):
    caplog.setLevel(logging.DEBUG, logger=heart_beat_task.env.log.name)
    heart_beat_task.wake_up(*args)
    expected_messages = [
        'applying config',
        'stop existing ticker',
        'ticker is disabled',
        'Heart beat: ',
    ]
    assert has_log_message(caplog, expected_messages)
