#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracMacroPost',
    version = '0.1',
    packages = ['macropost'],
    package_data={ 'macropost' : [ ] },
    author = "Noah Kantrowitz",
    author_email = "coderanger@yahoo.com",
    description = "Allow wiki macros to use POSTs",
    license = "BSD",
    keywords = "trac plugin wiki",
    url = "http://trac-hacks.org/wiki/MacroPostPlugin",

    entry_points = {
        'trac.plugins': [
            'macropost.web_ui = macropost.web_ui',
        ],
    },

    install_requires = [ ],
)
