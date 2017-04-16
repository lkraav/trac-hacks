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
    name='Navigation Plugin', 
    version='0.2.0',
    author = 'Franz Mayer, Gefasoft AG',
    author_email = 'franz.mayer@gefasoft.de', 
    description = 'Adds user option for displaying navigation menu as fixed menu or other navigation options.',
        license = "BSD 3-Clause",
    url = 'http://www.gefasoft-muenchen.de',
    download_url = 'http://trac-hacks.org/wiki/NavigationPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        navigationplugin = navigationplugin
    """,
    package_data={'navigationplugin': ['templates/*.*',
                                       'htdocs/*.css',
                                       'htdocs/*.js', 
                                       'locale/*.*',
                                       'locale/*/LC_MESSAGES/*.*']}
)

