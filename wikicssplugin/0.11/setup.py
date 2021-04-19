#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracWikiCssPlugin',
    version='0.3.1',
    packages=['tracwikicss'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="Wiki pages as CSS files Trac Plugin.",
    url='https://www.trac-hacks.org/wiki/WikiCssPlugin',
    license='GPLv3',
    zip_safe=False,
    install_requires=['Trac'],
    keywords='trac plugin wiki css',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': ['tracwikicss.plugin = tracwikicss.plugin']}
)
