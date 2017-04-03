#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import sys
from setuptools import find_packages, setup

extra = {}

try:
    import babel
except ImportError:
    babel = None
else:
    extractors = [
        ('**.py', 'python', None),
        ('**/templates/**.html', 'genshi', None),
        ('**/templates/**.js', 'javascript', None),
        ('**/templates/**.txt', 'genshi',
         {'template_class': 'genshi.template:NewTextTemplate'}),
    ]
    extra['message_extractors'] = {
        'ticketlog': extractors,
    }

setup(
    name='TracTicketChangelogPlugin',
    version='1.0.0',
    description="Show changelogs in trac ticket",
    author="Richard Liao",
    author_email="richard.liao.i@gmail.com",
    url="https://trac-hacks.org/wiki/TracTicketChangelogPlugin",
    license="3-Clause BSD",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
    include_package_data=True,
    package_data={'ticketlog': ['*.txt', 'templates/*.*', 'htdocs/*.*',
                                'tests/*.*', 'locale/*.*',
                                'locale/*/LC_MESSAGES/*.*']},
    zip_safe=False,
    keywords="trac plugin",
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac',
                      sys.version_info < (2, 6) and 'simplejson' or ''],
    entry_points="""
    [trac.plugins]
    ticketlog = ticketlog.web_ui
    """,
    **extra
)
