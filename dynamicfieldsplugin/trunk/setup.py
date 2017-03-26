#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2014 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

extra = {}

try:
    from trac.util.dist import get_l10n_cmdclass

    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            'dynfields': extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass

PACKAGE = 'TracDynamicFields'
VERSION = '2.2.1'

setup(
    name=PACKAGE, version=VERSION,
    description='Dynamically hide, default, copy, clear,' +
                ' validate, set ticket fields',
    author="Rob Guttman",
    author_email="guttman@alum.mit.edu",
    license='3-Clause BSD',
    url='http://trac-hacks.org/wiki/DynamicFieldsPlugin',
    packages=['dynfields'],
    package_data={'dynfields': [
        'templates/*.html', 'htdocs/*.js', 'htdocs/*.css',
        'locale/*/LC_MESSAGES/*.mo', 'locale/.placeholder'
    ]},
    entry_points={'trac.plugins': ['dynfields.rules = dynfields.rules',
                                   'dynfields.web_ui = dynfields.web_ui']},
    test_suite='dynfields.tests.test_suite',
    tests_require=[],
    install_requires=['Trac'],
    extras_require={'Babel': 'Babel>= 0.9.5'},
    **extra
)
