#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from setuptools import setup, find_packages
from pkg_resources import parse_version

extra = {}

setup(
    name='TracFewFixesPlugin',
    version='0.12.0.1',
    description='Provide fixes for no longer fixed or delayed tickets',
    license='BSD',  # the same as Trac
    url='http://trac-hacks.org/wiki/TracFewFixesPlugin',
    author='Jun Omae',
    author_email='jun66j5@gmail.com',
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'tracfewfixes': ['htdocs/*.js'],
    },
    test_suite='tracfewfixes.tests.suite',
    zip_safe=True,
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'tracfewfixes.wiki = tracfewfixes.wiki',
            'tracfewfixes.web_ui = tracfewfixes.web_ui',
        ],
    },
    **extra)
