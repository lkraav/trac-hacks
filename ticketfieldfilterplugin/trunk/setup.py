#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2011-2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2016-2021 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TicketFieldFilter',
    version='1.1',
    packages=['ticketfieldfilter'],
    author='Cinc-th',
    author_email='',
    description='Filter ticket fields depending on ticket type and user permissions.',
    long_description="""A Trac plugin that filters ticket fields depending on the ticket type and
    permissions of the user. Shown fields can be made read only.""",
    license='3-Clause BSD',
    keywords='trac plugin filter ticket field',
    url='https://trac-hacks.org/wiki/TicketFieldFilterPlugin',
    package_data={'ticketfieldfilter': ['templates/*', 'htdocs/css/*.css', 'htdocs/js/*.js']},
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'ticketfieldfilter.web_ui = ticketfieldfilter.web_ui',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)
