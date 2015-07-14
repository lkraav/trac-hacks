#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008 Alec Thomas
# Copyright (C) 2009-2015 Michael Renzmann <mrenzmann@otaku42.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracHacks',
    version='3.0',
    author='Alex Thomas',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description='Customizations of the trac-hacks site.',
    license='3-Clause BSD',
    url='https://trac-hacks.org/wiki/TracHacksPlugin',
    packages=['trachacks'],
    package_data={
        'trachacks': [
            'templates/*.html', 'htdocs/js/*.js',
            'htdocs/css/*.css', 'htdocs/png/*.png',
            'default-pages/*',
        ]
    },
    dependency_links=[
        'http://trac-hacks.org/svn/voteplugin/trunk'
        '#egg=TracVote-0.3dev',
        'http://trac-hacks.org/svn/svnauthzadminplugin/1.0'
        '#egg=SvnAuthzAdminPlugin-1.0dev',
    ],
    entry_points={
        'trac.plugins': [
            'trachacks.db = trachacks.db',
            'trachacks.macros = trachacks.macros',
            'trachacks.web_ui = trachacks.web_ui',
        ]
    },
    install_requires=[
        'Trac',
        'TracAccountManager',
        'TracTags >= 0.7',
        'TracVote >= 0.3',
        'SvnAuthzAdminPlugin',
    ],
    test_suite='trachacks.tests.test_suite',
)
