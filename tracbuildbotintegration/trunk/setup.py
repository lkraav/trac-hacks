#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Etienne PIERRE <e.ti.n.pierre_AT_gmail.com>
#
# TracBuildbot is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# TracBuildbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

from setuptools import setup

setup(
    name='TracBuildbot',
    version='0.2.0',
    author='Etienne PIERRE',
    description='A plugin to integrate Buildbot into Trac',
    url='https://trac-hacks.org/wiki/TracBuildbotIntegration',
    license='GPL',
    packages=['tracbb'],
    package_data={'tracbb': [
        'htdocs/*.css',
        'htdocs/*.png',
        'templates/*.html'
    ]},
    entry_points={
        'trac.plugins': 'tracbb = tracbb.tracbb'
    },
)
