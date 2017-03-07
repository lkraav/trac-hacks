#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Sebastian Benthall
# Copyright (C) 2009 Jeff Hammel
# Copyright (C) 2010 Rowan Wookey
# Copyright (C) 2012-2013 Daniel Kahn Gillmor <dkg@fifthhorseman.net>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

version = '1.2.0'

setup(name='TracSensitiveTickets',
      version=version,
      description="A trac plugin that lets you mark tickets as 'sensitive' "
                  "with a check box.  Those tickets can only be seen with "
                  "permission.",
      author='Jeff Hammel, Sebastian Benthall, Rowan Wookey, '
             'Daniel Kahn Gillmor',
      author_email='dkg@fifthhorseman.net',
      maintainer='Daniel Kahn Gillmor',
      maintainer_email='dkg@fifthhorseman.net',
      url='https://trac-hacks.org/wiki/SensitiveTicketsPlugin',
      keywords='trac plugin security',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      zip_safe=False,
      entry_points="""
      [trac.plugins]
      sensitivetickets = sensitivetickets
      """,
      install_requires=['Trac'],
      )
