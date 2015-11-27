#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2012 Lars Wireen <lw@agitronic.se>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup


setup(name='SharedCookieAuth',
      version='0.1.5',
      description="share cookies between trac projects in the same directory",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      maintainer='Lars Wireen',
      maintainer_email='lw@agitronic.se',
      url='https://trac-hacks.org/wiki/SharedCookieAuthPlugin',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      zip_safe=False,
      entry_points="""
      [trac.plugins]
      sharedcookieauth = sharedcookieauth.sharedcookieauth
      """,
      )
