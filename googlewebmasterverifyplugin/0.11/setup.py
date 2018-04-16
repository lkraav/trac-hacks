#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracGoogleWebmasterVerifyPlugin',
    version='0.3',
    packages=['tracgooglewebmasterverify'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="GoogleWebmasterVerify Plugin for Trac",
    url='https://www.trac-hacks.org/wiki/GoogleWebmasterVerifyPlugin',
    license='GPLv3',
    zip_safe=False,
    install_requires=['Trac'],
    keywords='trac google webmaster verify wiki plugin',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracgooglewebmasterverify.plugin = tracgooglewebmasterverify.plugin']}
)
