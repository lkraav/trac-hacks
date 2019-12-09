#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Yoshiyuki Sugimoto <s.yosiyuki@gmail.com>
# Copyright (C) 2012-2013 Jun Omae <jun66j5@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracBookmark',
    version='1.0.0',
    author='Yoshiyuki Sugimoto',
    maintainer='Yoshiyuki Sugimoto',
    maintainer_email='s.yosiyuki@gmail.com',
    description='A plugin bookmark Trac resources.',
    license='3-clause BSD',
    url='https://trac-hacks.org/wiki/BookmarkPlugin',
    install_requires=['Trac'],
    exclude_package_data={'': ['tests/*']},
    test_suite='tracbookmark.tests.test_suite',
    classifiers=['Framework :: Trac'],
    packages=['tracbookmark'],
    package_data={'tracbookmark': [
        'templates/*.html',
        'htdocs/*.*',
        'htdocs/js/*.js',
        'htdocs/css/*.css'
    ]},
    entry_points = {'trac.plugins': ['tracbookmark = tracbookmark']},
)
