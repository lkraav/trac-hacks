#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracGoogleStaticMapMacro',
    version='1.1',
    packages=['tracgooglestaticmap'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="GoogleStaticMap Trac Macro.",
    url='https://www.trac-hacks.org/wiki/GoogleStaticMapMacro',
    license='GPLv3',
    zip_safe=False,
    install_requires=['Trac', 'TracAdvParseArgsPlugin'],
    keywords='trac google static map macro',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracgooglestaticmap.macro = tracgooglestaticmap.macro']}
)
