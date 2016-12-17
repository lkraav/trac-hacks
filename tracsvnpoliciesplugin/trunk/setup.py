#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'TracSVNPoliciesPlugin'
VERSION = '1.0'

setup(name=PACKAGE, version=VERSION,
      author='Andrei Culapov',
      author_email='aculapov@optaros.com',
      url='https://trac-hacks.org/wiki/TracSvnPoliciesPlugin',
      description='Policy management for SVN repositories',
      license='BSD',
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
