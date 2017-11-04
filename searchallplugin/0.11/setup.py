#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2010 Alvaro J. Iradier <alvaro.iradier@polartech.es>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracSearchAll',
    version='0.9',
    packages=['tracsearchall'],
    author='Alvaro J. Iradier',
    author_email="alvaro.iradier@polartech.es",
    description="Search in all projects in the same parent folder",
    long_description="",
    license='GPL',
    url="https://www.trac-hacks.org/wiki/SearchAllPlugin",
    entry_points={
        'trac.plugins': [
            'tracsearchall = tracsearchall.searchall'
        ]
    }
)
