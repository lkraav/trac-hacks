#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name = 'TracHideChanges',
    version = '1.0.0',
    packages = ['hidechanges'],
    package_data = { 'hidechanges': ['templates/*.html'] },

    author = 'Rob Guttman',
    author_email = 'guttman@alum.mit.edu',
    description = 'Hide ticket changes based on configurable rules.',
    license = '3-Clause BSD',
    keywords = 'trac plugin hide changes',
    url = 'http://trac-hacks.org/wiki/HideChangesPlugin',
    classifiers = [
        'Framework :: Trac',
    ],

    install_requires = [],

    entry_points = {
        'trac.plugins': [
            'hidechanges.web_ui = hidechanges.web_ui',
        ]
    },
)
