#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracWikiAutoComplete',
    version = '1.4',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Auto-completes wiki formatting',
    classifiers=['Framework :: Trac'],
    license='BSD',
    url='https://trac-hacks.org/wiki/WikiAutoCompletePlugin',
    packages = ['wikiautocomplete'],
    package_data = {'wikiautocomplete': [
            'htdocs/js/*.js',
            'htdocs/css/*.css',
        ]
    },

    entry_points = {'trac.plugins': [
            'wikiautocomplete.web_ui = wikiautocomplete.web_ui',
        ]
    },
)
