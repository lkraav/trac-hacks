#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrei Culapov <aculapov@optaros.com>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

PACKAGE = 'TracSVNPoliciesPlugin'
VERSION = '1.0'

setup(name=PACKAGE, version=VERSION,
      author='Andrei Culapov',
      author_email='aculapov@optaros.com',
      url='https://trac-hacks.org/wiki/TracSvnPoliciesPlugin',
      description='Policy management for SVN repositories',
      license='3-Clause BSD',
      packages=['svnpolicies'],
      package_data={
          'svnpolicies': [
              'svnpolicy.conf',
              'README',
              'htdocs/css/*.css',
              'htdocs/js/*.js',
              'templates/*.html',
              'hooks/*.py'
          ]
      },
      entry_points={
            'trac.plugins': [
                'svnpolicies.admin = svnpolicies.admin'
            ]
      },
      eager_resources=[
          'hooks/post-commit.py',
          'hooks/pre-commit.py',
          'hooks/pre-revprop-change.py',
          'hooks/loader.py'
      ],
      install_requires = ['Trac'],
      zip_safe=True,
      )
