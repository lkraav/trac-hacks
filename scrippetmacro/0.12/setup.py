#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracScrippetsMacro',
    version = '0.8.1',
    packages = ['scrippets'],
    package_data={ 'scrippets' : [ 
                                   'htdocs/css/*.css', 
                                   'htdocs/js/*.js',
                                   'templates/*.html'
                                 ] },
    author = "Benjamin Lau",
    description = "Macro to add scrippets/Fountain to a wiki page and a IHTMLPreviewRenderer for Final Draft Pro v8 XML.",
    license = "BSD",
    keywords = "trac plugin macro comments renderer",
    url = "http://trac-hacks.org/wiki/ScrippetsMacro",
    classifiers = [
        'Framework :: Trac',
    ],
    
    entry_points = {
        'trac.plugins': [
            'scrippets.macro = scrippets.macro',
            'scrippets.render = scrippets.render',
        ],
    },
)
