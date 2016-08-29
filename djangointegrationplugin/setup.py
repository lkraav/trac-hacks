#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Guilhelm Savin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

PACKAGE = 'DjangoIntegration'
VERSION = '1.1'

setup(name=PACKAGE,
      version=VERSION,
      author='Guilhelm Savin',
      license='3-Clause BSD',
      packages=['djangointegration'],
      entry_points = """
        [trac.plugins]
        djangointegration = djangointegration.auth
      """
)
