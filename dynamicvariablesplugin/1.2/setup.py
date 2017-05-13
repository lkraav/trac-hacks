#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

PACKAGE = 'TracDynamicVariables'
VERSION = '1.2.0'

setup(
    name=PACKAGE, version=VERSION,
    description='Default and convert report dynamic variables to pulldowns',
    author="Rob Guttman",
    author_email="guttman@alum.mit.edu",
    license='3-Clause BSD',
    url='https://trac-hacks.org/wiki/DynamicVariablesPlugin',
    packages = ['dynvars'],
    package_data = {'dynvars': ['htdocs/*.js']},
    entry_points = {'trac.plugins': ['dynvars.web_ui = dynvars.web_ui']}
)
