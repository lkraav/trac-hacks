#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'TracUnixGroups',
    version = '0.2',
    packages = ['unixgroups'],
    author = "Noah Kantrowitz",
    author_email = "noah@coderanger.net",
    description = "Use UNIX groups in Trac",
    long_description = "Allows permissions to be assigned based on local system groups",
    license = "BSD",
    keywords = "trac plugin unix groups permissions",
    url = "https://trac-hacks.org/wiki/UnixGroupsPlugin",
    classifiers = ['Framework :: Trac'],
    entry_points = {
        'trac.plugins': [
            'unixgroups.unixgroups = unixgroups.unixgroups'
        ]
    }
)

