#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracNumberedHeadlinesPlugin',
    version='0.5',
    packages=['tracnumberedheadlines'],
    author='Martin Scharrer',
    package_data={
        'tracnumberedheadlines': ['htdocs/*.css'],
    },
    author_email='martin@scharrer-online.de',
    description="Trac Plug-in to add numbered headlines.",
    url='http://www.trac-hacks.org/wiki/NumberedHeadlinesPlugin',
    license='GPLv3',
    zip_safe=False,
    keywords='trac numbered headlines plugin',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracnumberedheadlines.plugin = tracnumberedheadlines.plugin']}
)
