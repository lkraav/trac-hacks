#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracGoogleSitemapPlugin',
    version='1.1',
    packages=['tracgooglesitemap'],
    author='Martin Scharrer',
    author_email='martin@scharrer-online.de',
    description="Plugin to generate Google Sitemaps (version for Trac 0.11)",
    url='https://www.trac-hacks.org/wiki/GoogleSitemapPlugin',
    license='GPLv3',
    zip_safe=False,
    keywords='trac google sitemap plugin',
    install_requires=['Trac'],
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'tracgooglesitemap.plugin = tracgooglesitemap.plugin',
        'tracgooglesitemap.notify = tracgooglesitemap.notify'
    ]}
)
