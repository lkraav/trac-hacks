#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 falkb
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracComponentHierarchy',
    version='1.2.0',
    packages=['componenthierarchy'],
    package_data={
        'componenthierarchy': [
            'htdocs/*.js',
            'htdocs/css/*.css',
        ]
    },
    author='falkb',
    author_email='tdoering@baumer.com',
    maintainer='falkb',
    license="3-Clause BSD",
    url='https://trac-hacks.org/wiki/ComponentHierarchyPlugin',
    description='Add a hierarchy to the component field',
    long_description='ComponentHierarchy',
    keywords='ticket component hierarchy',
    install_requires=['Trac'],
    entry_points={'trac.plugins': ['componenthierarchy = componenthierarchy']}
)
