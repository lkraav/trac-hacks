#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2014 Tetsuya Morimoto <tetsuya.morimoto@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

version = '0.4.6'

try:
    long_description = ''.join([
        open('README.md').read(),
        open('changelog').read(),
    ])
except:
    long_description = ''

setup(
    name='TracAutocompleteUsersPlugin',
    version=version,
    description='complete the known trac users, AJAX style',
    long_description=long_description,
    author='Jeff Hammel',
    author_email='jhammel@openplans.org',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    url='https://trac-hacks.org/wiki/AutocompleteUsersPlugin',
    keywords='trac plugin',
    license='BSD 3-Clause',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
    include_package_data=True,
    install_requires=['Trac'],
    tests_require=['tox'],
    package_data={'autocompleteusers': [
        'htdocs/css/*.css', 'htdocs/css/*.gif', 'htdocs/js/*.js']
    },
    zip_safe=False,
    classifiers=[
        'Framework :: Trac',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    entry_points="""
    [trac.plugins]
    autocompleteusers = autocompleteusers.autocompleteusers
    """,
)
