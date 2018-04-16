#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracAddHeadersPlugin',
    version='0.4',
    packages=['tracaddheaders'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description='AddHeaders Trac Plugin.',
    url='https://www.trac-hacks.org/wiki/AddHeadersPlugin',
    license='GPLv3',
    zip_safe=False,
    keywords='trac plugin addheaders',
    install_requires=['Trac'],
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracaddheaders.plugin = tracaddheaders.plugin']}
)
