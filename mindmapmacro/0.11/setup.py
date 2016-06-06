#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]


setup(
    name = 'TracMindMapMacro',
    version = '0.5',
    packages = ['tracmindmap'],
    package_data = {
        'tracmindmap' : [ 'htdocs/*.swf', 'htdocs/*.js', 'htdocs/*.css', 'htdocs/images/*' ],
    },
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Trac Macro to display Freemind mindmaps using a Flash app.",
    url = 'https://www.trac-hacks.org/wiki/MindMapMacro',
    license      = 'GPLv3',
    zip_safe     = False,
    keywords = 'trac mindmap freemind flash macro',
    install_requires = ['TracExtractUrl', 'Trac'],
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': [
      'tracmindmap.macro = tracmindmap.macro',
     ]}
)
