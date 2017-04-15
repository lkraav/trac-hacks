#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='TracDiscussion',
      version='1.2',
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
      install_requires=['Trac'],
      extras_require={'spamfilter': ['TracSpamFilter >= 1.2'],
                      'tags': ['TracTags >= 0.9']},
      test_suite='tracdiscussion.tests.test_suite',
      tests_require=[],
      )
