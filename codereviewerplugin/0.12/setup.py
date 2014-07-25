#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

PACKAGE = 'TracCodeReviewer'
VERSION = '0.0.3'

setup(
    name=PACKAGE, version=VERSION,
    description='Reviews changesets and updates ticket with results',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='3-Clause BSD', url='http://trac-hacks.org/wiki/CodeReviewerPlugin',
    packages=['coderev'],
    package_data={'coderev': ['templates/*.html',
                              'htdocs/*.css',
                              'htdocs/*.js',
                              'upgrades/*.py',
                              'util/*.py']},
    entry_points={'trac.plugins': ['coderev.api = coderev.api',
                                   'coderev.web_ui = coderev.web_ui',]}
)
