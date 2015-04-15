# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Jay Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='detailedView', version='1.1',
    packages=find_packages(exclude=['*.tests*']),
    author='Jay Thomas',
    license='BSD 3-Clause',
    entry_points = """
        [trac.plugins]
        detailedView = detailedView
    """,
    package_data={'detailedView': ['templates/*.html']},
)
