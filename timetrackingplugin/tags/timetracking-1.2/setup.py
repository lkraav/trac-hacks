#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TimeTracking',
    version = '1.2',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Track time by planning estimates and logging spent hours',
    packages = ['timetracking', 'timetracking.upgrades'],
    package_data = {'timetracking': [
            'templates/*.html',
            'htdocs/*.js',
            'htdocs/chosen/*.js',
            'htdocs/chosen/*.css',
            'htdocs/chosen/*.png',
        ]
    },
    extras_require={
        'WeekPlan': 'WeekPlan >= 1.1',
    },
    entry_points = {'trac.plugins': [
            'timetracking.core = timetracking.core',
            'timetracking.web_ui = timetracking.web_ui',
            'timetracking.chart = timetracking.chart',
            'timetracking.weekplanevents = timetracking.weekplanevents[WeekPlan]',
        ]
    },
)
