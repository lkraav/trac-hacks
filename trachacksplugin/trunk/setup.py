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
    maintainer='Michael Renzmann',
    maintainer_email='mrenzmann@otaku42.de',
    description='Customizations of the trac-hacks site.',
    license='3-Clause BSD',
    url='http://trac-hacks.org/wiki/TracHacksPlugin',
    packages=['trachacks'],
    package_data={
        'trachacks': [
            'templates/*.html', 'htdocs/js/*.js',
            'htdocs/css/*.css', 'htdocs/*.gif',
            'htdocs/png/*.png',
            ]
        },
    dependency_links=[
        'http://trac-hacks.org/svn/tagsplugin/trunk#egg=TracTags-0.7',
        'http://trac-hacks.org/svn/accountmanagerplugin/trunk#egg=TracAccountManager-0.5dev',
        'http://trac-hacks.org/svn/voteplugin/trunk#egg=TracVote-0.3dev',
        'http://trac-hacks.org/svn/svnauthzadminplugin/0.12#egg=SvnAuthzAdminPlugin',
        ],
    entry_points={
        'trac.plugins': [
            'trachacks.macros = trachacks.macros',
            'trachacks.web_ui = trachacks.web_ui',
            ]
        },
    install_requires=[
        'TracAccountManager',
        'TracTags >= 0.7',
        'TracVote >= 0.2',
        'SvnAuthzAdminPlugin',
        ],
    test_suite='trachacks.tests.test_suite',
    )
