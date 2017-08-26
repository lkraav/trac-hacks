#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008 Alex Thomas
# Copyright (C) 2010-2017 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(name='TracPoll',
      version='0.4.0',
      packages=['tracpoll'],
      entry_points={'trac.plugins': ['tracpoll = tracpoll']},
      author='Alec Thomas',
      maintainer='Ryan J Ollos',
      maintainer_email='ryan.j.ollos@gmail.com',
      url='https://trac-hacks.org/wiki/PollMacro',
      license='3-Clause BSD',
      package_data={'tracpoll': ['htdocs/css/*.css']},
      install_requires=['Trac'],
      )
