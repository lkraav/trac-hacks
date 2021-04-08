#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Optaros, Inc
#

from setuptools import setup

setup(name='TracSectionEditPlugin',
      version='1.3.0',
      packages=['tracsectionedit'],
      author='Catalin Balan',
      author_email='cbalan@optaros.com',
      url='https://trac-hacks.org/wiki/SectionEditPlugin',
      description="Edit sections of the Trac wiki",
      install_requires=['Trac'],
      license='BSD',
      entry_points={'trac.plugins': [
          'tracsectionedit.web_ui = tracsectionedit.web_ui',
      ]},
      package_data={'tracsectionedit': ['htdocs/js/*.js']}
      )
