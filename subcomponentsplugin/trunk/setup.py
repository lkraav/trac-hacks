#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, Niels Sascha Reedijk <niels.reedijk@gmail.com>
# All rights reserved. Distributed under the terms of the MIT License.
#

from setuptools import setup

setup(
    name='TracSubcomponents',
    version='1.3.1',
    packages=['subcomponents'],
    package_data={'subcomponents': [
        'htdocs/*.js',
        'templates/*.html',
    ]},
    author='Niels Sascha Reedijk',
    author_email='niels.reedijk@gmail.com',
    description='Provides support for subcomponents in the interface.',
    license='MIT',
    keywords='trac plugin ticket query components',
    url='https://trac-hacks.org/wiki/SubcomponentsPlugin',
    classifiers=[
        'Framework :: Trac',
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    install_requires=['Trac>=1.0dev', ],

    entry_points={
        'trac.plugins': [
            'subcomponents.components_view = subcomponents.components_view',
            'subcomponents.web_ui = subcomponents.web_ui',
        ]
    }
)
