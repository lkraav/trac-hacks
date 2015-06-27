#!/usr/bin/env python

from setuptools import setup

PACKAGE = 'IncludeAttachment'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['includeattachment'],
      entry_points={'trac.plugins': '%s = includeattachment' % PACKAGE},
)
