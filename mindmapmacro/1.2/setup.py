#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracMindMapMacro',
    version = '1.2.0',
    packages = ['tracmindmap'],
    author = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description = "Trac Macro to display Freemind mindmaps using a Flash app.",
    url = 'https://www.trac-hacks.org/wiki/MindMapMacro',
    license = 'GPLv3',
    zip_safe = False,
    keywords = 'trac mindmap freemind flash macro',
    install_requires = ['TracExtractUrl', 'Trac'],
    dependency_links=[
        'https://trac-hacks.org/svn/extracturlplugin/0.11#egg=TracExtractUrl',
    ],
    package_data = {
        'tracmindmap': [
            'htdocs/*.swf',
            'htdocs/*.js',
            'htdocs/images/*.png',
        ],
    },
    classifiers = ['Framework :: Trac'],
    entry_points = {'trac.plugins': [
        'tracmindmap.macro = tracmindmap.macro',
    ]}
)
