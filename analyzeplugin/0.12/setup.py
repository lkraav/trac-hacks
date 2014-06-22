#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2014 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

PACKAGE = 'TracAnalyze'
VERSION = '0.0.9'

setup(
    name=PACKAGE, version=VERSION,
    description='Analyzes tickets for dependency and other problems',
    author="Rob Guttman", author_email="guttman@alum.mit.edu",
    license='3-Clause BSD', url='http://trac-hacks.org/wiki/AnalyzePlugin',
    packages = ['analyze'],
    package_data = {'analyze':['analyses/*.py','templates/*.html',
                               'htdocs/*.css','htdocs/*.js']},
    entry_points = {'trac.plugins':['analyze.web_ui = analyze.web_ui',
                                    'analyze.analysis = analyze.analysis']}
)
