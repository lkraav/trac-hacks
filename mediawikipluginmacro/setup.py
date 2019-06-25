#!/usr/bin/python
from setuptools import setup

setup(
    name = "TracMediaWikiMacro",
    version = "1.1",
    packages = ['mediawiki'],
    entry_points = {'trac.plugins': 'mediawiki = mediawiki'}
)
