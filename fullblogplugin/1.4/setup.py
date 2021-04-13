# -*- coding: utf-8 -*-
"""
Trac plugin proving a full-featured, self-contained Blog.

License: BSD

(c) 2007 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from setuptools import setup

setup(name='TracFullBlog',
      version='0.2.0',
      packages=['tracfullblog'],
      author='CodeResort.com = BV Network AS',
      author_email='simon-code@bvnetwork.no',
      keywords='trac blog',
      description='Full-featured and self-contained Blog plugin for Trac.',
      url='https://trac-hacks.org/wiki/FullBlogPlugin',
      license='BSD',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Plugins',
                   'Environment :: Web Environment',
                   'Framework :: Trac',
                   'License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   ],
      zip_safe = False,
      extras_require={
            'tags': 'TracTags>=0.11',
            'spamfilter': 'TracSpamFilter>=1.4dev'},
      entry_points={'trac.plugins': [
            'tracfullblog.admin = tracfullblog.admin',
            'tracfullblog.core = tracfullblog.core',
            'tracfullblog.db = tracfullblog.db',
            'tracfullblog.macros = tracfullblog.macros',
            'tracfullblog.spamfilter = tracfullblog.spamfilter[spamfilter]',
            'tracfullblog.tags = tracfullblog.tags[tags]',
            'tracfullblog.web_ui = tracfullblog.web_ui']},
      package_data={'tracfullblog' : ['htdocs/*.png',
                                      'htdocs/css/*.css',
                                      'htdocs/js/*.js',
                                      'templates/*.html',
                                      'templates/*.rss', ]},
      exclude_package_data={'': ['tests/*']},
      test_suite = 'tracfullblog.tests.test_suite',
      tests_require = [],
      install_requires = [])
