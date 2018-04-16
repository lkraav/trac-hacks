#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracDashesSyntaxPlugin',
    version='1.1',
    packages=['tracdashessyntax'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="Trac Plug-in to add Wiki syntax for em and en dashes.",
    url='https://www.trac-hacks.org/wiki/DashesSyntaxPlugin',
    license='GPLv3',
    zip_safe=False,
    keywords='trac plugin wiki syntex dash em en',
    install_requires=['Trac'],
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracdashessyntax.plugin = tracdashessyntax.plugin']}
)
