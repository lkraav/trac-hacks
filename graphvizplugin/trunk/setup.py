# -*- coding: utf-8 -*-
#
# Copyright (c) 2005, 2006, 2008 Peter Kropf. All rights reserved.
#
# $Id$


from setuptools import setup, find_packages


with open('README.rst') as f:
    long_description = f.read()

setup (
    name = 'TracGraphviz',
    version = '1.4.0.1',
    author = "Peter Kropf",
    author_email = "pkropf@gmail.com",
    packages = find_packages(),
    package_data = {
        'graphviz': ['examples/*']
    },
    entry_points={'trac.plugins': 'graphviz = graphviz.graphviz'},
    install_requires = ['Trac', 'Genshi'],
    keywords = "trac graphviz",
    url = "https://trac-hacks.org/wiki/GraphvizPlugin",
    description = "Graphviz plugin for Trac 1.4",
    long_description = long_description,
    long_description_content_type = 'text/x-rst',
    license = "BSD 3-Clause",
)
