#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracDownloads',
    version='1.0.0',
    author="Radek Bartoň",
    author_email="blackhex@post.cz",
    maintainer="Ryan J Ollos",
    maintainer_email="ryan.j.ollos@gmail.com",
    url='https://trac-hacks.org/wiki/DownloadsPlugin',
    description='Project release downloads plugin for Trac',
    license="GPL",
    keywords="trac downloads",
    packages=['tracdownloads', 'tracdownloads.db'],
    package_data={'tracdownloads': [
        'templates/*.html',
        'htdocs/css/*.css'
    ]},
    install_requires=['Trac'],
    extras_require={'Tags': ['TracTags']},
    entry_points={'trac.plugins': [
        'TracDownloads.api = tracdownloads.api',
        'TracDownloads.core = tracdownloads.core',
        'TracDownloads.init = tracdownloads.init',
        'TracDownloads.webadmin = tracdownloads.webadmin',
        'TracDownloads.consoleadmin = tracdownloads.consoleadmin',
        'TracDownloads.wiki = tracdownloads.wiki',
        'TracDownloads.timeline = tracdownloads.timeline',
        'TracDownloads.tags = tracdownloads.tags[Tags]'
    ]},
)
