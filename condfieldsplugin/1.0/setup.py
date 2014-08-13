#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracCondFields',
    version='3.0',
    packages=['condfields'],
    package_data={'condfields': ['templates/*.html', 'htdocs/*.js']},

    author='Noah Kantrowitz',
    author_email='noah@coderanger.net',
    description='Support for conditional fields in different ticket types.',
    license='3-Clause BSD',
    keywords='trac plugin ticket conditional fields',
    url='http://trac-hacks.org/wiki/CondFieldsPlugin',
    classifiers=[
        'Framework :: Trac',
    ],

    extras_require={'customfieldadmin': 'TracCustomFieldAdmin'},

    entry_points={
        'trac.plugins': [
            'condfields.web_ui = condfields.web_ui',
            'condfields.admin = condfields.admin[customfieldadmin]',
        ]
    },
)
