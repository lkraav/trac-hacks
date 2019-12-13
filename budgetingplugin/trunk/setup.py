#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 Franz Mayer Gefasoft AG
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='TracBudgeting',
    version='0.6.8',
    author='Gefasoft AG, Franz Mayer',
    author_email='franz.mayer@gefasoft.de',
    description='Possibility to add budgeting information '
                '(estimation, cost, user) to tickets',
    license='3-Clause BSD',
    url='https://trac-hacks.org/wiki/BudgetingPlugin',
    packages=find_packages(exclude=['*.tests*']),
    classifiers=['Framework :: Trac'],
    entry_points="""
        [trac.plugins]
        ticketbudgeting = ticketbudgeting
    """,
    install_requires=['Trac'],
    package_data={'ticketbudgeting': [
        'htdocs/js/*.js',
        'locale/*.*',
        'locale/*/LC_MESSAGES/*.*'
    ]},
)
