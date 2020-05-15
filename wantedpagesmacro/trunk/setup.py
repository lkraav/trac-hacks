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
    name='TracWantedPages',
    version='0.6.0',
    author='Justin Francis',
    author_email='jfrancis@justinfrancis.org',
    maintainer='Geert Linders',
    maintainer_email='glinders@dynamiccontrols.com',
    description="List all TracLinks non-existent wiki pages.",
    license='BSD 3-Clause',
    packages=['wantedpages'],
    url='https://trac-hacks.org/wiki/WantedPagesMacro',
    entry_points={
        'trac.plugins': [
            'wantedpages.macro = wantedpages.macro',
        ]
    },
    test_suite='wantedpages.tests.test_suite',
)
