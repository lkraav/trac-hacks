#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martin Aspeli <optilude@gmail.com>
# Copyright (C) 2012 Chris Nelson <Chris.Nelson@SIXNET.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TeamCalendar',
    author='Martin Aspeli',
    author_email='optilude@gmail.com',
    maintainer='Chris Nelson',
    maintainer_email='Chris.Nelson@SIXNET.com',
    description='Trac plugin for managing team availability',
    version='1.0.0',
    license='3-Clause BSD',
    url='https://trac-hacks.org/wiki/TeamCalendarPlugin',
    packages=['teamcalendar'],
    package_data={'teamcalendar': ['templates/*.html',
                                   'htdocs/css/*.css', ]},
    entry_points={
        'trac.plugins': [
            'teamcalendar = teamcalendar.calendar'
        ]
    },
    install_requires=['Trac'],
)
