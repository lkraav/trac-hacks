#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracDateField',
    version='3.0.0',
    author='Noah Kantrowitz',
    author_email='noah@coderanger.net',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description='Add custom date fields to Trac tickets.',
    license='3-Clause BSD',
    keywords='trac plugin ticket',
    url='https://trac-hacks.org/wiki/DateFieldPlugin',
    packages=['datefield'],
    package_data={'datefield': [
        'htdocs/css/*.css',
        'htdocs/js/*.js', 'htdocs/css/images/*.png'
    ]},
    install_requires=['Trac'],
    classifiers=[
        'Framework :: Trac',
    ],
    entry_points={
        'trac.plugins': [
            'datefield.filter = datefield.filter',
        ]
    },
)
