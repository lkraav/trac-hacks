#!/usr/bin/env python

from setuptools import setup

setup(name='TracKeywordReplace',
      version='0.1',
      packages=['keywordreplace'],
      author='Bangyou Zheng',
      description='Replace keywords with wiki format from a table in a Wiki page.',
      url='http://trac-hacks.org/wiki/KeywordReplacePlugin',
      license='BSD',
      entry_points = {'trac.plugins': ['keywordreplace = keywordreplace']})
