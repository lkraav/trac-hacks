#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Alec Thomas
# Copyright (C) 2010-2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name = 'TracChangeLog',
    version = '0.4',
    packages = ['changelog'],
    author = 'Alec Thomas',
    maintainer = 'Ryan Ollos',
    maintainer_email = 'ryan.j.ollos@gmail.com',
    description = 'Adds a Wiki macro that displays the changelog for a repository path',
    keywords = 'trac scm macro plugin',
    license = '3-Clause BSD',
    url = 'https://trac-hacks.org/wiki/ChangeLogMacro',
    entry_points = {
        'trac.plugins':[
            'changelog.ChangeLogMacro = changelog.ChangeLogMacro'
        ]
    },
    install_requires = ['Trac'],
)
