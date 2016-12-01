#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2013 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracSumFields',
    version='2.0.0',
    packages=['sumfields'],
    package_data={'sumfields': ['htdocs/*.js']},

    author='Rob Guttman',
    author_email='guttman@alum.mit.edu',
    description='Sum fields in Trac custom queries.',
    license='3-Clause BSD',
    keywords='trac plugin sum',
    url='https://trac-hacks.org/wiki/SumFieldsPlugin',
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'sumfields.web_ui = sumfields.web_ui',
        ]
    },
)
