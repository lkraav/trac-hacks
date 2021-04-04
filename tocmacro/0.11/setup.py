#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Alec Thomas
# Copyright (C) 2006 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2007 Christian Boos <cboosr@neuf.fr>
# Copyright (C) 2007-2008 Odd Simon Simonsen <simon-code@bvnetwork.no>
# Copyright (C) 2008 Michael Jouvin <jouvin@lal.in2p3.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup


setup(
    name='TracTocMacro',
    version='12.0.0',
    packages=['tractoc'],
    author="Alec Thomas",
    maintainer="",
    maintainer_email="",
    description="A macro to create tables of contents.",
    long_description="""A macro to create a table of contents for either a
                        single page, or a collection of pages.""",
    license="BSD 3-Clause",
    keywords="trac plugin table of content macro",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    url="https://trac-hacks.org/wiki/TocMacro",
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'tractoc.macro = tractoc.macro'
        ]
    },
)
