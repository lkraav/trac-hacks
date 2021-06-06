#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import os.path
from setuptools import setup


setup(
    name='TracTweakTheme',
    packages=['tractheme'],
    version='0.1.0',
    author='Cinc-th',
    author_email='',
    maintainer='Cinc-th',
    maintainer_email='',
    description='A collection of themes modifying the Trac default theme.',
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README')).read(),
    long_description_content_type='text/markdown',
    keywords='wiki',
    url='https://trac-hacks.org/wiki/TracTweakTheme',
    license='BSD 3-Clause',
    package_data={'tractheme': ['htdocs/css/*.css',
                                'htdocs/js/*.js',
                                'templates/*.html',
                                'templates/genshi/*.html',
                                ]},
    entry_points={'trac.plugins': ['tractheme = tractheme',
                                   ]},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires=['Trac', 'TracThemeEngine'],
)
