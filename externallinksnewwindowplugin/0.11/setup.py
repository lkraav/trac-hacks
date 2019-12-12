#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='TracExtLinksNewWindow',
    version='1.2',
    description='Trac plugin to open external links in a new window.',
    license='GPLv3',
    zip_safe=False,
    url='https://trac-hacks.org/wiki/ExternalLinksNewWindow',
    download_url='https://pypi.python.org/pypi/ExternalLinksNewWindowPlugin',
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    classifiers=['Framework :: Trac'],
    packages=['tracextlinksnewwindow'],
    package_data={
        'tracextlinksnewwindow': ['htdocs/*.js'],
    },
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'tracextlinksnewwindow.plugin = tracextlinksnewwindow.plugin',
        ],
    }
)
