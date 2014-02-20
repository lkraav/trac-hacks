#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup


setup(name='FlexibleReporterNotification',
      version='0.1',
      author='Ryan J Ollos',
      author_email='ryan.j.ollos@gmail.com',
      license='3-Clause BSD',
      packages=['flexiblereporternotification'],
      url='http://trac-hacks.org/wiki/FlexibleReporterNotificationPlugin',
      author='Satyam',
      entry_points={
          'trac.plugins': 'flexiblereporternotification=flexiblereporternotification.api'
      }
)
