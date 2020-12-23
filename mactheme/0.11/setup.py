#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# Copyright (c) 2010 Olemis Lang. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from setuptools import setup

setup(
  name = 'TracMacOSTheme',
  version = '1.0.3',
  author = "Olemis Lang",
  author_email = 'olemis+trac@gmail.com',
  maintainer = 'Olemis Lang',
  maintainer_email = 'olemis+trac@gmail.com',
  description = "Trac theme to make it look like Mac OS",
  license = "GNU GPL v2",
  keywords = "trac plugin theme",
  url = "http://trac-hacks.org/wiki/TracMacTheme",
  packages = ['tracmacos'],
  package_data = {'tracmacos': ['htdocs/*.*', 'templates/*.*']},
  classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: MacOS X',
        'Environment :: MacOS X :: Aqua',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Natural Language :: Spanish',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: Software Development :: User Interfaces',
    ],
  install_requires = ['TracThemeEngine'],
  entry_points = {
      'trac.plugins': [
            'tracmacos.theme = tracmacos.theme',
        ]}
)
