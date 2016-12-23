#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 SIXNET, LLC
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

version = '1.2.0'

setup(name='RoadmapHours',
      version=version,
      description="Display estimated and actual hours in roadmap",
      long_description="""
Provides an implementation of ITicketGroupStatsProvider that uses
the actual and estimated hour fields from the Timing and Estimation
plugin to draw the roadmap stats.

You will need to set the status_provider under [roadmap] in trac.ini
to RoadmapHoursTicketGroupStatsProvider.
""",
      author='Joshua Hoke',
      author_email='',
      url='',
      keywords='trac plugin',
      license='3-Clause BSD',
      packages=['roadmaphours'],
      install_requires=['Trac', 'timingandestimationplugin'],
      zip_safe=False,
      entry_points="""
      [trac.plugins]
      roadmaphours = roadmaphours
      """
)
