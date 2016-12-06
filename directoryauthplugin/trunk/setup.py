#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
# Extended: Branson Matheson <branson.matheson@nasa.gov>
# Fixed: Stefan "Bebbo" Franke <bebbo@bejy.net>

from setuptools import setup

PACKAGE = 'TracDirectoryAuth'
VERSION = '2.0.2'

setup(
    name=PACKAGE,
    version=VERSION,
    author='John Hampton',
    author_email='pacopablo@pacopablo.com',
    maintainer='Branson Matheson',
    maintainer_email='branson.matheson@nasa.gov',
    description='Trac Authentication against LDAP or AD ',
    url='https://trac-hacks.org/wiki/DirectoryAuthPlugin',
    license='BSD',
    zip_safe=True,
    packages=['tracext', 'tracext.dirauth'],
    entry_points={
        'trac.plugins': [
            'dirauth.db = tracext.dirauth.db',
            'dirauth = tracext.dirauth',
            'dirauth.permissionstore = tracext.dirauth.api:UserExtensiblePermissionStore',
        ],
    },
    namespace_packages=['tracext'],
    install_requires=['Trac', 'TracAccountManager', 'python-ldap'],
)
