#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

version = '0.1.3'

setup(
    name='TicketMoverPlugin',
    version=version,
    description="move tickets from one Trac to a sibling Trac",
    author='Jeff Hammel',
    author_email='jhammel@openplans.org',
    url='https://trac-hacks.org/wiki/k0s',
    keywords='trac plugin',
    license="3-Clause BSD",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
    include_package_data=True,
    package_data={'ticketmoverplugin': ['templates/*', 'htdocs/*']},
    zip_safe=False,
    install_requires=[
        'TicketSidebarProvider',
    ],
    dependency_links=[
        "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
    ],
    entry_points="""
        [trac.plugins]
        ticketmoverplugin = ticketmoverplugin.ticketmover
        ticketmoverweb = ticketmoverplugin.web_ui
    """,
)
