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
    name='CondFieldsGenshiPlugin',
    version='0.3',
    author='Reinhard Wobst',
    author_email='rwobst@gmx.de',
    description="CondFieldsGenshiPlugin based on BlackMagicTicketTweaks",
    license="BSD 3-Clause",
    packages=find_packages(),
    package_data={'condfieldsgenshi': []},
    install_requires=['Trac'],
    entry_points={'trac.plugins': ['condfieldsgenshi = condfieldsgenshi']}
)
