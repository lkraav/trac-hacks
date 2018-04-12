#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name         = 'TracExtractUrl',
    version      = '0.4',
    packages     = ['tracextracturl'],
    author       = 'Martin Scharrer',
    author_email = 'martin@scharrer-online.de',
    description  = 'Provides `extract_url` method to extract the URL from TracWiki links.',
    url          = 'https://www.trac-hacks.org/wiki/ExtractUrlPlugin',
    download_url = 'https://pypi.python.org/pypi/TracExtractUrl',
    license      = 'GPLv3',
    keywords     = 'trac plugin extract url',
    classifiers  = ['Framework :: Trac'],
    zip_safe     = False,
    entry_points = {'trac.plugins': [
            'tracextracturl.macro      = tracextracturl.macro',
        ]
    }
)
