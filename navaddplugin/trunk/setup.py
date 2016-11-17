#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Michael Renzmann <mrenzmann@otaku42.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(name='NavAdd',
      version='0.4',
      packages=['navadd'],
      author='Michael Renzmann',
      author_email='mrenzmann@otaku42.de',
      license='3-Clause BSD',
      url='https://trac-hacks.org/wiki/NavAddPlugin',
      description='A plugin for adding navigation items into one of the navigation bars.',
      keywords='trac navigation main meta',
      entry_points={'trac.plugins': ['navadd.navadd = navadd.navadd']},
      package_data = {
          'navadd': [
              'htdocs/*.js',
          ],
      },
)
