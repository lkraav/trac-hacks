#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Giuseppe Ursino
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.


import os

from setuptools import setup

setup(
    name = 'TracRestrictAccess',
    version = '0.0.1',
    packages = ['restrictaccess'],

    author = 'Giuseppe Ursino',
    author_email = 'giuseppe.ursino@vimar.com',
    description = 'Restrict access to Trac System.',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = 'BSD 3-Clause',
    keywords = 'trac plugin wiki ticket permissions security',
    url = 'http://trac-hacks.org/wiki/TracRestrictAccessPlugin',
    download_url = 'http://trac-hacks.org/svn/tracrestrictaccessplugin/1.0#egg=TracRestrictAccess-dev',
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'restrictaccess.policy = restrictaccess.policy',
        ],
    },
)
