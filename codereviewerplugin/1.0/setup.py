#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

PACKAGE = 'TracCodeReviewer'
VERSION = '1.0.0'

setup(
    name=PACKAGE, version=VERSION,
    description='Reviews changesets and updates ticket with results',
    author="Rob Guttman",
    author_email="guttman@alum.mit.edu",
    license='3-Clause BSD',
    url='https://trac-hacks.org/wiki/CodeReviewerPlugin',
    packages=['coderev'],
    package_data={'coderev': ['htdocs/*.css',
                              'htdocs/*.js',
                              'upgrades/*.py',
                              'util/*.py']},
    entry_points={'trac.plugins': ['coderev.api = coderev.api',
                                   'coderev.web_ui = coderev.web_ui',]},
    install_requires=['Trac'],
    test_suite='coderev.tests',
)
