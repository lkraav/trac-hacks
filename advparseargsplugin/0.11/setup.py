#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 Martin Scharrer <martin@scharrer-online.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name         = 'TracAdvParseArgsPlugin',
    version      = '0.4',
    packages     = ['tracadvparseargs'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = "Advanced argument parser for Trac macros.",
    url          = 'http://www.trac-hacks.org/wiki/AdvParseArgsPlugin',
    license      = 'BSD 3-Clause',
    zip_safe     = False,
    keywords     = 'trac plugin parse argument',
    classifiers  = ['Framework :: Trac'],
    entry_points = {'trac.plugins': [
          'tracadvparseargs.macro     = tracadvparseargs.macro',
          'tracadvparseargs.parseargs = tracadvparseargs.parseargs',
      ]}
)

