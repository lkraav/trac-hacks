#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Chris Nelson <Chris.Nelson@SIXNET.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='TicketCreateButtons', version='0.1',
    author="Chris Nelson",
    author_email="Chris.Nelson@SIXNET.com",
    license="3-Clause BSD",
    packages=find_packages(exclude=['*.tests*']),
    url="http://trac-hacks.org/wiki/TicketCreateButtonsPlugin",
    entry_points = """
        [trac.plugins]
        ticketCreateButtons=ticketCreateButtons
    """,
)
