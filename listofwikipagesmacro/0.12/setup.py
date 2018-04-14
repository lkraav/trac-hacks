#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracListOfWikiPagesMacro',
    version='0.5',
    packages=['traclistofwikipages'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    package_data={
        'traclistofwikipages': ['htdocs/*.css'],
    },
    description="ListOfWikiPagesMacro for Trac v0.12",
    url='https://www.trac-hacks.org/wiki/ListOfWikiPagesMacro',
    license='GPLv3',
    zip_safe=False,
    install_requires='TracAdvParseArgsPlugin>=0.2',
    keywords='trac list wiki page macro',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'traclistofwikipages.macro = traclistofwikipages.macro']}
)
