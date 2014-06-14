#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Daniel Hambraeus
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup
import sys

name = 'TracJenkinsPlugin'
version = '1.0'
min_trac_version = '1.0'

# Check for minimum required Trac version
try:
    import trac
    if trac.__version__ < min_trac_version:
        print "%s %s requires Trac >= %s" % (name, version, min_trac_version)
        sys.exit(1)
except ImportError:
    print "Trac not found"
    sys.exit(1)

setup(
    name=name,
    version=version,
    packages=['tracjenkins'],
    author='Daniel Hambraeus',
    entry_points={
        'trac.plugins': [
            '%s = tracjenkins' % name],
    },
    package_data={
        'tracjenkins': ['templates/*.html',
                        'htdocs/css/*.css',
                        'htdocs/css/images/*.png',
                        'htdocs/js/*.js']

    },
    install_requires=['jenkinsapi'],
)
