#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'Table Sorter Plugin',
    version = '1.1',
    author = 'Peter Suter',
    author_email = 'petsuter@gmail.com',
    description = 'Allows sorting any wiki table',
    packages = ['tablesorter'],
    package_data = {'tablesorter': ['htdocs/*.*']},
    
    entry_points = {'trac.plugins': ['tablesorter = tablesorter']}
)
