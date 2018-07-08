#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2009 Prentice Wongvibulsin <me@prenticew.com>
# Copyright (c) 2010-2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(
    name='Tracticketstats',
    version='3.0.0',
    author='Prentice Wongvibulsin',
    author_email='me@prenticew.com',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    license='BSD 3-Clause',
    url='https://trac-hacks.org/wiki/TracTicketStatsPlugin',
    description='Visualize ticket statistics',
    packages=find_packages(exclude=['*.tests']),
    entry_points="""
        [trac.plugins]
        ticketstats.ticketstats = ticketstats.ticketstats
        ticketstats.macro = ticketstats.macro
    """,
    install_requires=['Trac', 'TracAdvParseArgsPlugin'],
    package_data={
        'ticketstats': [
            'htdocs/*.js',
            'templates/*.html'
        ]
    },
)
