#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
  name = 'TracDiscussion',
  version = '0.7',
  packages = ['tracdiscussion', 'tracdiscussion.db'],
  package_data = {'tracdiscussion' : ['templates/*.html', 'templates/*.txt', 'htdocs/css/*.css']},
  entry_points = {'trac.plugins': ['TracDiscussion.api = tracdiscussion.api',
    'TracDiscussion.core = tracdiscussion.core',
    'TracDiscussion.init = tracdiscussion.init',
    'TracDiscussion.wiki = tracdiscussion.wiki',
    'TracDiscussion.timeline = tracdiscussion.timeline',
    'TracDiscussion.admin = tracdiscussion.admin',
    'TracDiscussion.search = tracdiscussion.search',
    'TracDiscussion.notification = tracdiscussion.notification']},
  install_requires = [''],
  keywords = 'trac discussion',
  author = 'Radek Bartoň, Alec Thomas',
  author_email = 'blackhex@post.cz',
  url = 'http://trac-hacks.swapoff.org/wiki/DiscussionPlugin',
  description = 'Discussion forum plugin for Trac',
  license = '''GPL'''
)
