#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Clemens
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='InfoSnippetPlugin',
    version=0.3,
    description="Offers a box with ticket infos (to be copied into clipboard).",
    author="Clemens",
    author_email="",
    license="3-Clause BSD",
    url="https://trac-hacks.org/wiki/InfoSnippetPlugin",
    install_requires = ['Trac'],
    packages=find_packages(exclude=['*.tests*']),
    package_data={'infosnippet': ['htdocs/*.js', 'htdocs/*.css']},
    entry_points={'trac.plugins': ['infosnippet = infosnippet']}
)
