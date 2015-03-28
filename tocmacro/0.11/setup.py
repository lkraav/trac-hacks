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
    version='11.0.0.5',
    packages=['tractoc'],
    author="Alec Thomas",
    maintainer="Christian Boos",
    maintainer_email="cboosr@neuf.fr",
    description="A macro to create tables of contents.",
    long_description="""A macro to create a table of contents for either a
                        single page, or a collection of pages.""",
    license="BSD 3-Clause",
    keywords="trac plugin table of content macro",
    url="http://trac-hacks.org/wiki/TocMacro",
    entry_points={
        'trac.plugins': [
            'tractoc.macro = tractoc.macro'
        ]
    },
)
