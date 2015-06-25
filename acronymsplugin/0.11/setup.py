#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(name='TracAcronyms',
      version='0.2',
      packages=['tracacronyms'],
      author='Alec Thomas',
      description='Auto-generated acronyms from a table in a Wiki page.',
      url='https://trac-hacks.org/wiki/AcronymsPlugin',
      license='3-Clause BSD',
      entry_points = {'trac.plugins': ['tracacronyms = tracacronyms']},
      install_requires = ['Trac'],
      test_suite='tracacronyms.tests'
)
