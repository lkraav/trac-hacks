#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

PACKAGE = 'TracQuiet'
VERSION = '1.0.1'

setup(
    name=PACKAGE,
    version=VERSION,
    description='Toggles quiet (no email) mode for Announcer plugin',
    author="Rob Guttman",
    author_email="guttman@alum.mit.edu",
    license='GPL',
    url='http://trac-hacks.org/wiki/TracQuietPlugin',
    packages=['quiet'],
    package_data={'quiet': ['htdocs/*.js', 'htdocs/*.css', 'htdocs/*.png']},
    entry_points={'trac.plugins': ['quiet.web_ui = quiet.web_ui']}
)
