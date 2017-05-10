#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracNavigationMenu',
    version = '1.0',
    packages = ['tracnavmen'],
    #package_data = { 'toc': ['templates/*.cs','htdocs/*' ] },

    author = "Vegard Stenstad",
    #author_email = "",
    maintainer = "Vegard Stenstad",
    maintainer_email = "vegard@beider.org",
    description = "A combined SubWiki and TOCMacro plugin.",
    long_description = """Creates a TOC menu for subtrees""",
    license = "BSD",
    keywords = "trac plugin table of content macro subtree",
    url = "http://trac-hacks.org/wiki/",

    entry_points = {
        'trac.plugins': [
            'tracnavmen.macro = tracnavmen.macro'
        ]
    },
)
