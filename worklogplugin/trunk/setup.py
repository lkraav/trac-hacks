#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2012 Colin Guthrie <trac@colin.guthr.ie>
# Copyright (c) 2011-2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import sys
from setuptools import find_packages, setup
from pkg_resources import parse_version

name = 'WorkLog'
version = '1.0'
min_trac = '1.0'
try:
    import trac
except ImportError:
    pass
else:
    if parse_version(trac.__version__) < parse_version(min_trac):
        print("%s %s requires Trac >= %s" % (name, version, min_trac))
        sys.exit(1)

setup(
    name=name,
    description='Plugin to track tickets users are working',
    keywords='trac plugin ticket working',
    version=version,
    url='https://trac-hacks.org/wiki/WorklogPlugin',
    license='http://www.opensource.org/licenses/mit-license.php',
    author='Colin Guthrie',
    author_email='trac@colin.guthr.ie',
    long_description="""
    I'll write this later!
    """,
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'worklog': [
            'htdocs/*.css',
            'htdocs/*.js',
            'htdocs/*.png',
            'templates/*.html'
        ]
    },
    entry_points={
        'trac.plugins': [
            'worklog.admin = worklog.admin',
            'worklog.api = worklog.api',
            'worklog.ticket_daemon = worklog.ticket_daemon',
            'worklog.ticket_filter = worklog.ticket_filter',
            'worklog.timeline = worklog.timeline',
            'worklog.xmlrpc = worklog.xmlrpc[xmlrpc]',
            'worklog.webui = worklog.webui'
        ]
    },
    extras_require={'xmlrpc': 'TracXMLRPC >= 1.1'},
)
