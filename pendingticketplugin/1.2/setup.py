#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2013 Daniel Atallah <datallah@pidgin.im>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracPendingTicket',
    version='1.2.0',
    packages=['removepending'],

    author='Daniel Atallah',
    author_email='datallah@pidgin.im',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    description="""
    Switch from 'pending' status to a configurable status when the
    reporter responds to a ticket.
    """,
    long_description="""
    A Trac plugin that will switch the ticket status from 'pending' to the value stored in:

    [ticket]
    pending_removal_status = new

    when the reporter responds to it.
    """,
    license='BSD',
    keywords='trac plugin pending ticket',
    url='https://trac-hacks.org/wiki/PendingTicketPlugin',
    install_requires=['Trac'],
    classifiers=[
        'Framework :: Trac',
    ],
    entry_points={
        'trac.plugins': [
            'removepending.remove_pending = removepending.remove_pending',
        ],
    }
)
