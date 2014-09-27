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

min_python = (2, 4)
if sys.version_info < min_python:
    print("TracTicketTemplate requires Python %d.%d or later" % min_python)
    sys.exit(1)

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
    version="0.2",
    description="Show changelogs in trac ticket",
    author="Richard Liao",
    author_email="richard.liao.i@gmail.com",
    url="http://trac-hacks.org/wiki/TracTicketChangelogPlugin",
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
    install_requires=[sys.version_info < (2, 6) and 'simplejson' or ''],
    entry_points="""
    [trac.plugins]
    ticketlog = ticketlog.web_ui
    """,
    **extra
)
