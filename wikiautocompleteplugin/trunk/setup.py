#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'WikiAutoComplete',
    version = '1.1',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Auto-completes wiki formatting',
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
