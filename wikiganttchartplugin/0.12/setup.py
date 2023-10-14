#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

if __name__ != '__main__':
    raise ImportError

from setuptools import find_packages, setup

extra = {}
try:
    from trac.util.dist import get_l10n_js_cmdclass
except ImportError:
    pass
else:
    cmdclass = get_l10n_js_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
            ('templates/*.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            'wikiganttchart': extractors,
        }

setup(
    name='WikiGanttChartPlugin',
    version='0.12.0.5',
    author='OpenGroove,Inc.',
    author_email='info@opengroove.com',
    maintainer='Jun Omae',
    maintainer_email='jun66j5@gmail.com',
    url='https://trac-hacks.org/wiki/WikiGanttChartPlugin',
    description='Provide simple Gantt chart with an editor in Trac wiki',
    license='BSD',  # the same as Trac
    classifiers=[
        'Framework :: Trac',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    zip_safe=True,
    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'wikiganttchart': [
            'htdocs/js/*.js',
            'htdocs/js/*.map',
            'htdocs/js/locale/*.js',
            'htdocs/css/*.*',
            'htdocs/css/images/*.*',
            'htdocs/fonts/*.*',
            'locale/*/LC_MESSAGES/*.mo',
            'templates/genshi/*.html',
            'templates/jinja2/*.html',
        ],
    },
    test_suite='wikiganttchart.tests.suite',
    entry_points={
        'trac.plugins': [
            'wikiganttchart.web_ui = wikiganttchart.web_ui',
        ],
    },
    **extra)
