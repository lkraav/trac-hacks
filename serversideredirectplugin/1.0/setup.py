#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracServerSideRedirectPlugin',
    version='1.0.0',
    packages=['tracserversideredirect'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="Server side redirect plugin for Trac.",
    url='https://www.trac-hacks.org/wiki/ServerSideRedirectPlugin',
    license='GPLv3 or 3-Clause BSD',
    zip_safe=False,
    keywords='trac plugin server redirect',
    classifiers=['Framework :: Trac'],
    dependency_links=[
        'https://trac-hacks.org/svn/extracturlplugin/0.11'
        '#egg=TracExtractUrl-0.3'],
    install_requires=['TracExtractUrl>=0.3'],
    entry_points={'trac.plugins': [
        'tracserversideredirect.plugin = tracserversideredirect.plugin']}
)
