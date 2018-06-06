#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Theodor Norup <theodor.norup@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup, find_packages

PACKAGE = 'TracYetAnotherChartMacro'
VERSION = '0.2.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Graph SQL queries using the Plotly javascript library',
    author="Theodor Norup", author_email="theodor.norup@gmail.com",
    license='3-Clause BSD',
    url='http://trac-hacks.org/wiki/TracYetAnotherChartMacro',
    packages = ['yachart'],
    package_data = {'yachart':[
            'htdocs/*.js',
            ]
    },
    entry_points = {'trac.plugins':['yachart.web_ui = yachart.web_ui']}
)
