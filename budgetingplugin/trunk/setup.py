#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 Franz Mayer Gefasoft AG
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Budgeting Plugin',
    version='0.6.5',
    author = 'Gefasoft AG, Franz Mayer',
    author_email = 'franz.mayer@gefasoft.de',
    description = 'Possibility to add budgeting information (estimation, cost, user) to tickets',
    license = "BSD 3-Clause",
    url = 'http://trac-hacks.org/wiki/BudgetingPlugin',
    download_url = 'https://trac-hacks.org/wiki/BudgetingPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        ticketbudgeting = ticketbudgeting
    """,
    package_data={'ticketbudgeting': ['htdocs/js/*.js',
                                      'locale/*.*',
                                      'locale/*/LC_MESSAGES/*.*']},
)

