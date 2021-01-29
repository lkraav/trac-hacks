#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Thomas Vander Stichele <thomas at apestaart dot org>
# Copyright (C) 2010-2020 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2021 Clemens Feige
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='TracKeywordsPlugin',
    version=1.0,
    description="Allows adding and removing keywords on a ticket from a list",
    author="Thomas Vander Stichele",
    author_email="thomas at apestaart dot org",
    maintainer = "Clemens Feige"
    license="BSD",
    url="https://trac-hacks.org/wiki/TracKeywordsPlugin",
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'trackeywords': [
            'htdocs/*.js', 'htdocs/*.css',
            'README', 'TODO', 'ChangeLog'
        ]
    },
    entry_points="""
        [trac.plugins]
        trackeywords = trackeywords.web_ui
    """,
)
