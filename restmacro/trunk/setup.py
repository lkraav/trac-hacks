#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2016 Philippe Normand <phil@base-art.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import inspect
from setuptools import setup

from tracrst import __author__, __version__, __license__

setup(
    name = 'ReST',
    version = __version__,
    packages = ['tracrst'],
    author = __author__,
    description = "ReST Wiki macro",
    #long_description = inspect.getdoc(TracReSTMacro),
    long_description = "The ReST Wiki macro translates ReST files hosted on the Subversion repository to HTML snippets.",
    license = __license__,
    keywords = "trac rst macro",
    url = "https://trac-hacks.org/wiki/ReSTMacro",
    entry_points = {
        'trac.plugins': [
            'tracrst.macro = tracrst.macro',
        ]
    },
)
