#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Alex Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(name='TracRepoSearch',
      version='0.2',
      packages=['tracreposearch'],
      author='Alec Thomas',
      maintainer='Ryan J Ollos',
      maintainer_email='ryano@physiosonics.com',
      url='https://trac-hacks.org/wiki/TracRepoSearch',
      license='BSD',
      scripts=['update-index'],
      entry_points={'trac.plugins': ['tracreposearch = tracreposearch']}
      )
