# -*- coding: utf-8 -*-
import time

import pytest

time_now = time.time()


def pytest_funcarg__memory_history_store(request, component):
    memory_history_store = component['memory_history_store']
    return memory_history_store

@pytest.mark.parametrize("values", [
    [],

    [(object(), time_now + 1, time_now + 11, True)],

    [(object(), time_now + 2, time_now + 12, True),
     (object(), time_now + 3, time_now + 13, False),
     (object(), time_now + 4, time_now + 14, True),
     ],
])
def test_memory_history_store_basic_action(memory_history_store, values):
    init_num = len(memory_history_store.history)
    hist_value_num = len(values)
    for value in values:
        memory_history_store.addExecution(*value)
    current_num = init_num + hist_value_num
    assert current_num == len(memory_history_store.history)
    assert current_num == len(list(memory_history_store.getExecution()))
    memory_history_store.clear()
    assert 0 == len(memory_history_store.history)
