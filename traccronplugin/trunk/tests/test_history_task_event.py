# -*- coding: utf-8 -*-
import pytest


def pytest_funcarg__task(request, component):
    task = component['heart_beat_task']
    return task

def pytest_funcarg__memory_history_store(request, component):
    memory_history_store = component['memory_history_store']
    return memory_history_store

def pytest_funcarg__history_task_event(request, component):
    history_task_event = component['history_task_event']
    return history_task_event


def test_history_task_event_basic(history_task_event,
                                  task, memory_history_store):
    assert 'history_task_event' == history_task_event.getId()

    memory_history_store.clear()  # initialize
    # operate tasks
    try:
        history_task_event.onStartTask(task)
        history_task_event.onEndTask(task, True)
        assert 1 == len(list(memory_history_store.getExecution()))

        history_task_event.onStartTask(task)
        history_task_event.onEndTask(task, True)
        assert 2 == len(list(memory_history_store.getExecution()))
    finally:
        memory_history_store.clear()
