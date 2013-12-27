#!/usr/bin/env python
# -*- coding: utf-8 -*-
#### AUTHORS ####
## Primary Author:
## Colin Guthrie
## http://colin.guthr.ie/
## trac@colin.guthr.ie
## trac-hacks user: coling

import sys
from setuptools import find_packages, setup
from pkg_resources import parse_version

name = 'WorkLog'
version = '0.4'
min_trac = '1.0'
try:
    import trac
    if parse_version(trac.__version__) < parse_version(min_trac):
        print("%s %s requires Trac >= %s" % (name, version, min_trac))
        sys.exit(1)
except ImportError:
    pass

setup(
    name=name,
    description='Plugin to manage the which tickets users are currently working on',
    keywords='trac plugin ticket working',
    version=version,
    url='http://trac-hacks.org/wiki/WorklogPlugin',
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
    extras_require = {'xmlrpc': 'TracXMLRPC >= 1.1'}
)
