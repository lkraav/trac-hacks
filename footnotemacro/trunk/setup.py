#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Alex Thomas
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2010-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracFootNoteMacro',
    version='1.6.1',
    packages=['footnotemacro'],
    package_data={'footnotemacro': ['htdocs/*.css',
                                    'htdocs/*.js']},
    author='Noah Kantrowitz',
    author_email='noah@coderanger.net',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description='Add footnotes to a wiki page',
    license='3-Clause BSD',
    keywords='trac plugin',
    url='https://trac-hacks.org/wiki/FootNoteMacro',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'footnotemacro.macro = footnotemacro.macro',
        ]
    },
    test_suite='footnotemacro.tests.test_suite',
)
