#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'IncludeAttachment'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      license="BSD 3-Clause",
      packages=['includeattachment'],
      entry_points={'trac.plugins': '%s = includeattachment' % PACKAGE},
)
