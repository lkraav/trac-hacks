#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Jun Omae
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup, find_packages

extra = {}

setup(
    name='TracUsernameDecoratePlugin',
    version='0.12.0.1',
    description='Showing author information instead of username in Trac '
                '(t:#7339)',
    license='BSD',  # the same as Trac
    url='http://trac-hacks.org/wiki/UsernameDecoratePlugin',
    author='Jun Omae',
    author_email='jun66j5@gmail.com',
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'tracusernamedecorate': ['htdocs/*.css', 'htdocs/*.js'],
    },
    entry_points={
        'trac.plugins': [
            'tracusernamedecorate.web_ui = tracusernamedecorate.web_ui',
        ],
    },
    **extra)
