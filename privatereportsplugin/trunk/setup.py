#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Michael Henke <michael.henke@she.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#

from setuptools import find_packages, setup

setup(
    name='TracPrivateReports',
    version='1.3.0',
    packages=find_packages(),
    author='Michael Henke',
    author_email='michael.henke@she.net',
    description="""A trac plugin that lets you control which groups and
        users can view a report.""",
    license="BSD 3-Clause",
    keywords='trac plugin security report group user',
    url='https://trac-hacks.org/wiki/PrivateReportsPlugin',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    zip_safe=True,
    package_data={'privatereports': ['templates/*.html']},
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'PrivateReports = privatereports.privatereports',
        ],
    },
)
