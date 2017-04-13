#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from setuptools import setup

setup(
    name='TicketModifiedFiles',
    version='2.0.0',
    description='Trac plugin that lists the files that have been modified '
                'while resolving a ticket.',
    author='Emilien Klein',
    author_email='Emilien Klein <e2jk AT users DOT sourceforge DOT net>',
    license='BSD-ish (see the COPYING.txt file)',
    url='https://trac-hacks.org/wiki/TicketModifiedFilesPlugin',
    packages=['ticketmodifiedfiles'],
    package_data={
        'ticketmodifiedfiles': ['templates/*.html', 'htdocs/css/*.css',
                                'htdocs/js/*.js']},
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': ['ticketmodifiedfiles = ticketmodifiedfiles']},
)
