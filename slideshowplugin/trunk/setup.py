#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Alec Thomas
# Copyright (C) 2010-2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

themes = ['blue', 'default', 'dokuwiki', 'flower', 'i18n', 'pixel', 'yatil']

data = ['templates/*.html', 'htdocs/*.png'] + \
       ['htdocs/ui/%s/*.*' % theme for theme in themes]

setup(name='SlideShow',
      version='0.3',
      packages=['slideshow'],
      author='Alec Thomas',
      maintainer = 'Ryan J Ollos',
      maintainer_email = 'ryan.j.ollos@gmail.com',
      url='http://trac-hacks.org/wiki/SlideShowPlugin',
      license='3-Clause BSD',
      zip_safe = False,
      install_requires = ['trac >= 0.11'],
      entry_points = {'trac.plugins': ['slideshow = slideshow.slideshow']},
      package_data={'slideshow' : data}
      )
