#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name = 'TracGoogleMapMacro',
    version = '0.5.',
    packages = ['tracgooglemap'],
    author = 'Martin Scharrer',
    package_data = {
        'tracgooglemap' : [ 'htdocs/*.js', 'htdocs/*.css' ],
    },
    author_email = 'martin@scharrer-online.de',
    description = "GoogleMap Trac Macro.",
    url = 'http://www.trac-hacks.org/wiki/GoogleMapMacro',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac googlemap macro',
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': ['tracgooglemap.macro = tracgooglemap.macro']}
)
