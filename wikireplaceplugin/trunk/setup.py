#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Radu Gasler <miezuit@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from __future__ import with_statement

import os

from setuptools import setup


def readme():
    """Return README file contents."""
    with open(os.path.join(os.path.dirname(__file__), 'README')) as fd:
        return fd.read()


setup(
    name='TracWikiReplace',
    version='1.1.2',
    packages=['wikireplace'],
    package_data={'wikireplace': ['templates/*.html']},

    author='Radu Gasler',
    author_email='miezuit@gmail.com',
    description='Add simple support for replacing text in wiki pages',
    long_description=readme(),
    license='3-Clause BSD',
    keywords='trac plugin wiki page search replace',
    url='https://trac-hacks.org/wiki/WikiReplacePlugin',
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'wikireplace.web_ui = wikireplace.web_ui',
        ],
    },
)
