#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Alec Thomas
# Copyright (C) 2006-2011 Radek Bartoň
# Copyright (C) 2012-2017 Ryan Ollos
# Copyright (C) 2013 Markus Decke
# Copyright (C) 2014 Steffen Hoffmann
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(name='TracDiscussion',
      version='1.2.1',
      author='Radek Bartoň',
      author_email='blackhex@post.cz',
      license='GPL',
      url='https://trac-hacks.org/wiki/DiscussionPlugin',
      description='Discussion forum plugin for Trac',
      keywords='trac discussion e-mail',
      packages=['tracdiscussion', 'tracdiscussion.db'],
      package_data={'tracdiscussion': [
          'templates/*.html', 'templates/*.txt', 'templates/*.rss',
          'htdocs/css/*.css', 'htdocs/js/*.js', 'htdocs/*.png']
      },
      entry_points={'trac.plugins': [
          'TracDiscussion.admin = tracdiscussion.admin',
          'TracDiscussion.ajax = tracdiscussion.ajax',
          'TracDiscussion.api = tracdiscussion.api',
          'TracDiscussion.core = tracdiscussion.core',
          'TracDiscussion.init = tracdiscussion.init',
          'TracDiscussion.notification = tracdiscussion.notification',
          'TracDiscussion.spamfilter = tracdiscussion.spamfilter[spamfilter]',
          'TracDiscussion.tags = tracdiscussion.tags[tags]',
          'TracDiscussion.timeline = tracdiscussion.timeline',
          'TracDiscussion.wiki = tracdiscussion.wiki']
      },
      classifiers=['Framework :: Trac'],
      install_requires=['Trac'],
      extras_require={'spamfilter': ['TracSpamFilter >= 1.2'],
                      'tags': ['TracTags >= 0.9']},
      test_suite='tracdiscussion.tests.test_suite',
      tests_require=[],
      )
