#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009 Justin Francis <jfrancis@justinfrancis.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name="WantedPages", 
    version="0.4",
    author='Justin Francis',
    author_email='jfrancis@justinfrancis.org',
    maintainer='Justin Francis',
    maintainer_email='jfrancis@justinfrancis.org',
    description="List all TracLinks for which the wiki page doesn't exist",
    license="BSD 3-Clause",
    packages=['wantedpages'],
    url='http://trac-hacks.org/wiki/WantedPagesMacro',
    entry_points={
        'trac.plugins': [
            'wantedpages.macro = wantedpages.macro',
        ]
    },
    test_suite='wantedpages.tests.test_suite',
)
