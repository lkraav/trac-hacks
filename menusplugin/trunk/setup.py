#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2007-2008 Optaros, Inc
#

from setuptools import setup

setup(name='TracMenus',
      version='0.3.0',
      packages=['tracmenus'],
      author="Catalin Balan",
      author_email="cbalan@optaros.com",
      url="https://trac-hacks.org/wiki/MenusPlugin",
      description="Trac Menus",
      license="BSD",
      entry_points={'trac.plugins': [
          'tracmenus.web_ui = tracmenus.web_ui',
      ]},
      install_requires=['Trac'],
      classifiers=[
          'Framework :: Trac',
      ],
      package_data={'tracmenus': [
          'htdocs/js/*.js',
          'htdocs/css/*.css',
          'htdocs/images/*.png'
      ]}
      )
