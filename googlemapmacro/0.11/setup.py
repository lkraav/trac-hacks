#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracGoogleMapMacro',
    version='0.6',
    packages=['tracgooglemap'],
    author='Martin Scharrer',
    package_data={
        'tracgooglemap': ['htdocs/*.js', 'htdocs/*.css'],
    },
    author_email='martin@scharrer-online.de',
    description="GoogleMap Trac Macro.",
    url='https://www.trac-hacks.org/wiki/GoogleMapMacro',
    license='GPLv3',
    zip_safe=False,
    install_requires=['Trac', 'TracAdvParseArgsPlugin'],
    keywords='trac googlemap macro',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracgooglemap.macro = tracgooglemap.macro']}
)
