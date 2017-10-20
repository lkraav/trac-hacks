# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name = 'TracMermaid',
    version = '0.4.2',
    packages = find_packages(exclude=['*.tests*']),
    license = "BSD 3-Clause",
    entry_points = {
        'trac.plugins': [
            'tracmermaid = tracmermaid',
        ],
    },
    install_requires=['Trac'],
    package_data = {
        'tracmermaid': [
            'htdocs/*',
        ],
    },
)
