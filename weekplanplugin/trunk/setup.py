#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'WeekPlan',
    version = '1.0',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Week-by-week planning macro for calendar events',
    packages = ['weekplan'],
    package_data = {'weekplan': ['htdocs/js/*.js',
                                 'htdocs/css/*.css',]},

    entry_points = {'trac.plugins': [
            'weekplan.core = weekplan.core',
            'weekplan.macro = weekplan.macro',
        ]
    },
)
