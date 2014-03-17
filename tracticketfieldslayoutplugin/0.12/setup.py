#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup, find_packages

extra = {}
try:
    from trac.util.dist import get_l10n_cmdclass
except ImportError:
    pass
else:
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'genshi', None),
            ]
        extra['message_extractors'] = {
            'tracticketfieldslayout': extractors,
            }

setup(
    name='TracTicketFieldsLayoutPlugin',
    version='0.12.0.1',
    description='Allow to customize the layout of ticket fields in view and form',
    license='BSD',  # the same as Trac
    url='http://trac-hacks.org/wiki/TracTicketFieldsLayoutPlugin',
    author='OpenGroove,Inc.',
    author_email='trac@opengroove.com',
    maintainer='Jun Omae',
    maintainer_email='jun66j5@gmail.com',
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'tracticketfieldslayout': [
            'htdocs/*.*', 'templates/*.html', 'locale/*/LC_*/*.mo',
            ],
        },
    entry_points={
        'trac.plugins': [
            'tracticketfieldslayout.admin = tracticketfieldslayout.admin',
            'tracticketfieldslayout.api = tracticketfieldslayout.api',
            'tracticketfieldslayout.web_ui = tracticketfieldslayout.web_ui',
            ],
        },
    **extra)
