#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracAddCommentMacro',
    version='0.3',
    packages=['addcomment'],
    package_data={'addcomment': []},
    author="Alec Thomas",
    description="Macro to add comments to a wiki page.",
    license="3-Clause BSD",
    keywords="trac plugin macro comments",
    url="https://trac-hacks.org/wiki/AddCommentMacro",
    classifiers=[
        'Framework :: Trac',
    ],

    entry_points={
        'trac.plugins': [
            'addcomment.macro = addcomment.macro',
        ],
    },

    install_requires=['TracMacroPost>=0.2'],
)
