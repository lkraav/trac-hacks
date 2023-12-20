#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2023 Jun Omae
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup, find_packages

extra = {}

setup(
    name='TracWaveDromPlugin',
    version='0.2',
    packages=find_packages(exclude=['*.tests']),
    package_data={'tracwavedrom' : ['htdocs/*.*', 'htdocs/*/*.*']},
    author='Jun Omae',
    author_email='jun66j5@gmail.com',
    license='3-clause BSD',  # the same as Trac
    url='https://trac-hacks.org/wiki/WaveDromPlugin',
    description='Provides WaveDrom processor to render wavedrom drawings within Trac wiki page',
    classifiers=[
        'Framework :: Trac',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'trac.plugins': [
            'tracwavedrom.macro = tracwavedrom.macro',
        ],
    },
    install_requires=['Trac >= 0.11'],
    tests_require=[],
    **extra)
