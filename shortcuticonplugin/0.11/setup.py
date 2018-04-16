#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracShortcutIconPlugin',
    version='0.3',
    packages=['tracshortcuticon'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="Configurables shortcut icons for Trac.",
    url='https://www.trac-hacks.org/wiki/ShortcutIconPlugin',
    license='GPLv3',
    zip_safe=False,
    keywords='trac plugin favicon shortcuticon',
    install_requires=['Trac'],
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracshortcuticon.plugin = tracshortcuticon.plugin']}
)
