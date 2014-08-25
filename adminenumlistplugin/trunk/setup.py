#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Stepan Riha <trac@nonplus.net>
# Copyright (C) 2012-2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2012-2014 Jun Omae <jun66j5@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

setup(name='TracAdminEnumListPlugin',
      version='2.0',
      description="Adds drag-and-drop reordering to admin panel enum lists.",
      author='Stepan Riha',
      author_email='trac@nonplus.net',
      maintainer='Ryan J Ollos',
      maintainer_email='ryan.j.ollos@gmail.com',
      url='http://trac-hacks.org/wiki/AdminEnumListPlugin',
      keywords='trac plugin',
      license='3-Clause BSD',
      classifiers=[
          'Framework :: Trac',
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'License :: OSI Approved :: BSD License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
      ],
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      package_dir={'adminenumlistplugin': 'adminenumlistplugin'},
      include_package_data=True,
      package_data={'adminenumlistplugin': ['htdocs/*.js', 'htdocs/*/*.js']},
      zip_safe=False,
      entry_points="""
      [trac.plugins]
      adminenumlistplugin = adminenumlistplugin.adminenumlistplugin
      """,
      )
