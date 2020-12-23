# -*- coding: utf-8 -*-
import logging
import time

import pytest
from utils import has_log_message


def pytest_funcarg__ticker(request, env):
    from traccron.core import Ticker
    ticker = Ticker(env, 1, lambda: 'wake up')
    return ticker


def test_ticker_basic_action(ticker):
    try:
        assert ticker.timer.isAlive()
        assert 60 == ticker.timer.interval
        assert 'wake up' == ticker.callback()

        # stop timer, but still alive
        ticker.cancel()
        assert ticker.timer.isAlive()
    finally:
        # stop timer thread
        ticker.cancel(wait=True)
        assert not ticker.timer.isAlive()


def test_ticker_create_new_timer(ticker):
    try:
        assert ticker.timer.isAlive()
        prev_timer_id = id(ticker.timer)
        ticker.create_new_timer(wait=True, delay=10)
        assert prev_timer_id != id(ticker.timer)
        assert 10 == ticker.timer.interval
    finally:
        ticker.cancel(wait=True)


def test_ticker_wake_up(ticker, caplog):
    caplog.setLevel(logging.DEBUG, logger=ticker.env.log.name)
    try:
        ticker.callback = lambda: ticker.env.log.debug('only logging')
        ticker.create_new_timer(wait=True, delay=1)
        time.sleep(2)
        expected_messages = [
            'applying config',
            'stop existing ticker',
            'ticker is disabled',
            'create new ticker',
            'new ticker started',
            'ticker wake up',
            'only logging',
            'last wake up time ',
            'next wake up time ',
            'current time ',
            'adjusted wait',
            'create new ticker',
            'new ticker started',
        ]
        assert has_log_message(caplog, expected_messages)
    finally:
        ticker.cancel(wait=True)
