#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Alec Thomas
# Copyright (C) 2010-2011 Ryan Ollos
# Copyright (C) 2012-2014 Jun Omae
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(name='IniAdmin',
      version='0.3',
      packages=['iniadmin'],
      author='Alec Thomas',
      maintainer='Jun Omae',
      maintainer_email='jun66j5@gmail.com',
      description='Expose all TracIni options using the Trac config option API',
      url='http://trac-hacks.org/wiki/IniAdminPlugin',
      license='BSD',
      entry_points={'trac.plugins': ['iniadmin = iniadmin']},
      package_data={'iniadmin' : ['htdocs/css/*.css', 'templates/*.html', ]},
      test_suite='iniadmin.tests',
)
