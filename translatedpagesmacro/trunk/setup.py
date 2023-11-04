#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE = 'TranslatedPages'
VERSION = '1.6.0'

setup(
    name=PACKAGE,
    version=VERSION,
    author='Dirk Stöcker, Zhang Cong (ftofficer)',
    maintainer='Dirk Stöcker',
    maintainer_email='trachacks@dstoecker.de',
    url='https://trac-hacks.org/wiki/TranslatedPagesMacro',
    download_url='https://trac-hacks.org/wiki/TranslatedPagesMacro',
    license = 'BSD',
    packages=['translatedpages'],
    entry_points={
        'trac.plugins': [
            'TranslatedPages = translatedpages'
        ],
    },
)
