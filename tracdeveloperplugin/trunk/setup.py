#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# Copyright (C) 2015-2017 Ryan Ollos
# Copyright (C) 2012-2013 Olemis Lang
# Copyright (C) 2008-2009 Noah Kantrowitz
# Copyright (C) 2008 Christoper Lenz
# Copyright (C) 2007-2008 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracDeveloper',
    version='0.5.0',
    packages=['tracdeveloper', 'tracdeveloper.dozer'],
    author='Alec Thomas',
    maintainer='',
    maintainer_email='',
    description='Adds some features to Trac that are useful for developers',
    url='https://trac-hacks.org/wiki/TracDeveloperPlugin',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    entry_points = {
        'trac.plugins': [
            'developer = tracdeveloper.main',
            'developer.apidoc = tracdeveloper.apidoc',
            'developer.debugger = tracdeveloper.debugger',
            'developer.plugins = tracdeveloper.plugins',
            'developer.javascript = tracdeveloper.javascript',
            'developer.log = tracdeveloper.log',
            'developer.dozer = tracdeveloper.dozer',
        ]
    },
    install_requires=['Trac'],
    package_data = {
        'tracdeveloper' : [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/developer/*.html',
        ],
        'tracdeveloper.dozer' : [
            'htdocs/*.css',
            'htdocs/*.js',
            'templates/*.html',
        ],
    }
)
