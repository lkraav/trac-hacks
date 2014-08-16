#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TimeTracking',
    version = '1.0',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Track time by planning estimates and logging spent hours',
    packages = ['timetracking', 'timetracking.upgrades'],
    package_data = {'timetracking': [
            'templates/*.html',
            'htdocs/chosen/*.js',
            'htdocs/chosen/*.css',
            'htdocs/chosen/*.png',
        ]
    },
    entry_points = {'trac.plugins': [
            'timetracking.core = timetracking.core',
            'timetracking.web_ui = timetracking.web_ui',
        ]
    },
)
