#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas
# Copyright (C) 2006-2007 Christian Boos
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

PACKAGE = 'TracPyDoc'
VERSION = '0.11.2'

setup(
    name=PACKAGE,
    version=VERSION,
    author='Alec Thomas',
    author_email='alec@swapoff.org',
    maintainer = "Christian Boos",
    maintainer_email = "cboos@neuf.fr",
    description = "Browse Python documentation from within Trac.",
    long_description = """
    Browse Python documentation as prepared by the pydoc system
    from within Trac.""",
    license = "3-Clause BSD",
    keywords = "trac plugin python documentation pydoc",
    url='https://trac-hacks.swapoff.org/wiki/PyDocPlugin',
    packages=['tracpydoc'],
    package_data={'tracpydoc' : ['templates/*.html', 'htdocs/css/*.css']},

    entry_points = {
        'trac.plugins': [
            'tracpydoc.tracpydoc = tracpydoc.tracpydoc'
        ]
    },
    )
