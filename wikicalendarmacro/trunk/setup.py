#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2013 Steffen Hoffmann
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann

from setuptools import find_packages, setup

extra = {}

from trac.dist import get_l10n_cmdclass
try:
    from trac.dist import extract_python
except ImportError:
    extract_python = None

cmdclass = get_l10n_cmdclass()
if cmdclass:
    extra['cmdclass'] = cmdclass
    extractors = [
        ('**.py', 'trac.dist:extract_python', None)
    ]
    extra['message_extractors'] = {
        'wikicalendar': extractors,
    }


setup(
    name = "TracWikiCalendarMacro",
    version = "2.2.0",
    author = "Matthew Good",
    author_email = "trac@matt-good.net",
    maintainer = "Steffen Hoffmann",
    maintainer_email = "hoff.st@web.de",
    url = "https://trac-hacks.org/wiki/WikiCalendarMacro",
    description = "Configurable calendars for Trac wiki.",
    long_description = """
Display Milestones and Tickets in a calendar view, the days link to:
 - milestones (day in bold) if there is one on that day
 - a wiki page that has wiki_page_format (if exist)
 - create that wiki page, if it does not exist and
use page template (if exist) for that new page.
Many different presentations are possible by using a certain macro
with one or more of it's corresponding attributes.
""",
    keywords = "trac macro calendar milestone ticket",
    classifiers = ['Framework :: Trac'],

    license = """
        Copyright (c), 2010,2011.
        Released under the 3-clause BSD license after initially being under
        THE BEER-WARE LICENSE, Copyright (c) Matthew Good.
        See changelog in source for contributors.
        """,

    install_requires = ['Trac'],
    extras_require = {'Babel': 'Babel>= 0.9.5'},
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'wikicalendar': [
            'htdocs/*', 'locale/*/LC_MESSAGES/*.mo', 'locale/.placeholder',
        ]
    },
    test_suite = 'wikicalendar.tests.suite',
    zip_safe = True,
    entry_points = {
        'trac.plugins': [
            'wikicalendar = wikicalendar.macros',
        ]
    },
    **extra
)
