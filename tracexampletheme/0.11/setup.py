#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
  name = 'TracExampleTheme',
  version = '1.0',
  author = "Olemis Lang",
  author_email = 'flioops.project@gmail.com',
  maintainer = 'Olemis Lang',
  maintainer_email = \
                 'flioops.project@gmail.com',
  description = "Tema de ejemplo (Trac)",
  license = "GNU GPL v2",
  keywords = "trac plugin theme",
  url = "http://opensvn.csie.org/traccgi/swlcu",
  packages = ['extheme'],
  package_data = {'extheme': ['htdocs/*.*']},
  classifiers = [
      'Framework :: Trac',
    ],
  install_requires = ['TracThemeEngine'],
  entry_points = {
      'trac.plugins': [
            'extheme.theme = extheme.theme',
        ]}
)
