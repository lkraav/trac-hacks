#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Noah Kantrowitz <noah+pypi@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracOhlohBadge',
    version='1.1',
    packages=['ohlohbadge'],
    author='Noah Kantrowitz',
    author_email='noah+pypi@coderanger.net',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description='A Trac wiki macro to display Ohloh project badges.',
    license='BSD 3-Clause',
    keywords='trac plugin macro ohloh badge',
    url='https://trac-hacks.org/wiki/OhlohBadgeMacro',
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=[],
    entry_points={
        'trac.plugins': [
            'ohlohbadge.macro = ohlohbadge.macro',
        ]
    },
)
