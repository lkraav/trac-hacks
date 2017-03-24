# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name = 'TracCiteCode',
    version = '0.3.1',
    packages = find_packages(exclude=['*.tests*']),
    license = "BSD 3-Clause",
    url = 'https://trac-hacks.org/wiki/CiteCodeMacro',
    entry_points = {
        'trac.plugins': [
            'traccitecode = traccitecode',
        ],
    },
    package_data = {
        'traccitecode': [
            'htdocs/*',
        ],
    },
)
