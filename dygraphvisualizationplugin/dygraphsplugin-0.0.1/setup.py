#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Jon Ashley <trac@zelatrix.plus.com>
# All rights reserved.
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

PACKAGE = 'DygraphsVisualization'
VERSION = '0.0.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Graphs tables and other data using Dygraphs Visualization API',
    author="Jon Ashley", author_email="trac@zelatrix.plus.com",
    license='3-Clause BSD',
    url='http://trac-hacks.org/wiki/DygraphsVisualizationPlugin',
    packages = ['dyviz'],
    package_data = {'dyviz':['templates/*.html','htdocs/*.css','htdocs/*.js']},
    entry_points = {'trac.plugins':['dyviz.web_ui = dyviz.web_ui']}
)
