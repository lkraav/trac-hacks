#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name = 'TracSecureTickets',
    version = '0.1.4',
    packages = ['securetickets'],
    author = 'Rob Guttman',
    author_email = 'guttman@alum.mit.edu',
    description = 'Adds ticket security policy based on component.',
    license = '3-Clause BSD',
    keywords = 'trac plugin secure tickets permissions',
    url = 'http://trac-hacks.org/wiki/SecureTicketsPlugin',
    classifiers = [
        'Framework :: Trac',
    ],

    install_requires = [],

    entry_points = {
        'trac.plugins': [
            'securetickets.api = securetickets.api',
        ]
    },
)
