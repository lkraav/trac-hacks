#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracProjectMenu',
    version='2.0',
    packages=['projectmenu'],
    package_data={'projectmenu': ['htdocs/*.js']},

    author="Noah Kantrowitz",
    author_email="noah@coderanger.net",
    description="Provide a menu entry to switch between projects in TRAC_ENV_PARENT_DIR-type setup.",
    license="3-Clause BSD",
    keywords="trac plugin multiproject",
    url="http://trac-hacks.org/wiki/ProjectMenuPlugin",
    classifiers=[
        'Framework :: Trac',
    ],

    #install_requires = ['TracWebAdmin'],

    entry_points={
        'trac.plugins': [
            'projectmenu.web_ui = projectmenu.web_ui',
        ]
    }
)
