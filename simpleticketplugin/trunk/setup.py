#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2011-2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracSimpleTicket',
    version='5.0',
    packages=['simpleticket'],
    author='Noah Kantrowitz',
    author_email='noah+tracplugins@coderanger.net',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description='Restricted ticket entry form for Trac',
    long_description="""A Trac plugin that provides a configurable ticket
        entry form, with selected fields hidden from the user.""",
    license='3-Clause BSD',
    keywords='trac plugin restricted ticket',
    url='https://trac-hacks.org/wiki/SimpleTicketPlugin',
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'simpleticket.web_ui = simpleticket.web_ui',
        ],
    }
)
