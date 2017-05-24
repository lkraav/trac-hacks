#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, 2011, 2013 John Szakmeister
# Copyright (C) 2016 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup
import multiprojectbacklog

PACKAGE = 'MultiProjectBacklog'

with open('README.txt') as fd:
    long_description = fd.read()

setup(
    name=PACKAGE,
    version=multiprojectbacklog.get_version(),
    packages=['multiprojectbacklog'],
    package_data={
        'multiprojectbacklog': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/*.html',
        ]},
    entry_points={
        'trac.plugins': [
            'multiprojectbacklog = multiprojectbacklog.web_ui',
            'backlog_prefs = multiprojectbacklog.prefs',
        ]
    },
    install_requires=['Trac'],
    author="John Szakmeister, Cinc",
    author_email="",
    description="Enables Trac to be used for managing your ticket backlog. "
                "Works with SimpleMultiProject plugin.",
    long_description=long_description,
    url="https://trac-hacks.org/wiki/MultiProjectBacklogPlugin",
    license="BSD",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2 :: Only',
    ],
)
