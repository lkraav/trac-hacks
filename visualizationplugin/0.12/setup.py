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

PACKAGE = 'TracVisualization'
VERSION = '0.2'

setup(
    name=PACKAGE, version=VERSION,
    description='Graphs tables and other data using Google Visualization API',
    author="Rob Guttman",
    author_email="guttman@alum.mit.edu",
    license='3-Clause BSD',
    url='https://trac-hacks.org/wiki/VisualizationPlugin',
    classifiers = ['Framework :: Trac'],
    packages=['viz'],
    package_data={'viz':['templates/*.html','htdocs/*.css','htdocs/*.js']},
    entry_points={'trac.plugins':['viz.web_ui = viz.web_ui']}
)
