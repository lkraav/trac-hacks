#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='WikiCreateTicket',
    version='0.1.1',
    packages=['wikicreateticket'],
    package_data={'wikicreateticket' : []},
    test_suite='wikicreateticket.tests.suite',
    author='Yoshiyuki Sugimoto',
    maintainer='Yoshiyuki Sugimoto',
    maintainer_email='s.yosiyuki@gmail.com',
    license='BSD',
    url='https://trac-hacks.org/wiki/WikiCreateTicketPlugin',
    description='A plugin to assign new markup to create ticket.',
    entry_points = {'trac.plugins': ['wikicreateticket = wikicreateticket']},
    )
