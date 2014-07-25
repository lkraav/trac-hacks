#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

PACKAGE = 'TracQueues'
VERSION = '0.2.0'

setup(
    name=PACKAGE, version=VERSION,
    description='Manages ticket queues via drag-and-drop',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='3-Clause BSD', url='http://trac-hacks.org/wiki/QueuesPlugin',
    packages=['queues'],
    package_data={
        'queues': ['templates/*.html', 'htdocs/*.css', 'htdocs/*.js']
    },
    entry_points = {'trac.plugins': ['queues.web_ui = queues.web_ui']}
)
