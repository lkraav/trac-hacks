#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008, Stephen Hansen <shansen@advpubtech.com>
# Copyright (C) 2012-2013 Reinhard Wobst <rwobst@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name = 'CondFieldsGenshiPlugin',
    version = '0.2',
    author = 'Reinhard Wobst',
    author_email = 'rwobst@gmx.de',
    description = "CondFieldsGenshiPlugin for Trac >= 0.11 based on BlackMagicTicketTweaks",
    license = \
    """Copyright (C) 2012-2013, Reinhard Wobst. All rights reserved. Released under the 3-clause BSD license.""",
    packages = find_packages(),
    package_data = {'condfieldsgenshi' : []},
    install_requires = ['trac>=0.11'],
    entry_points = {'trac.plugins': ['condfieldsgenshi = condfieldsgenshi'] }
)
