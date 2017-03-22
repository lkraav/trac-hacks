#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracPrivateWiki',
    version = '1.1.0',
    packages = ['privatewiki'],

    author = "Eric Hodges",
    author_email = "eric.hodges@gmail.com",
    description = "Add private wiki ability.",
    maintainer = "Nathan Lewis",
    maintainer_email = "natewlew@gmail.com",
    long_description = "Allow admins to restrict access to wikis.",
    license = "BSD",
    keywords = "trac plugin wiki permissions security",
    url = "https://trac-hacks.org/wiki/PrivateWikiPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    entry_points = {
        'trac.plugins': [
            'privatewiki = privatewiki.api',
        ]
    }
)
