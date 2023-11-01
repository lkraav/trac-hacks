#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2023 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

if __name__ != '__main__':
    raise ImportError

from setuptools import setup, find_packages

extra = {}
try:
    import babel
    from trac.util.dist import get_l10n_cmdclass
except ImportError:
    pass
else:
    del babel
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass

setup(
    name='TracTicketFieldsLayoutPlugin',
    version='0.12.0.7',
    description='Allow to customize the layout of ticket fields in view and form',
    license='BSD',  # the same as Trac
    url='https://trac-hacks.org/wiki/TracTicketFieldsLayoutPlugin',
    author='OpenGroove,Inc.',
    author_email='trac@opengroove.com',
    maintainer='Jun Omae',
    maintainer_email='jun66j5@gmail.com',
    classifiers=[
        'Framework :: Trac',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'tracticketfieldslayout': [
            'htdocs/*.*', 'templates/*/*.html', 'locale/*/LC_*/*.mo',
        ],
    },
    test_suite='tracticketfieldslayout.tests.test_suite',
    entry_points={
        'trac.plugins': [
            'tracticketfieldslayout.admin = tracticketfieldslayout.admin',
            'tracticketfieldslayout.api = tracticketfieldslayout.api',
            'tracticketfieldslayout.web_ui = tracticketfieldslayout.web_ui',
        ],
    },
    **extra)
