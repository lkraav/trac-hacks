#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'Cards',
    version = '1.2',
    author = 'Peter Suter',
    author_email = 'peter@lucid.ch',
    description = 'Macro of interactive board for sorting cards in list',
    packages = ['cards', 'cards.upgrades'],
    package_data = {'cards': [
            'templates/*.html',
            'htdocs/js/*.js',
            'htdocs/css/*.css',
        ]
    },
    entry_points = {'trac.plugins': [
            'cards.core = cards.core',
            'cards.macro = cards.macro',
        ]
    },
)
