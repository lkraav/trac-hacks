#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

import re
from setuptools import setup, find_packages
import tracext.google.search as tg

setup(
    name = tg.__packagename__,
    version = tg.__version__,
    author = tg.__author__,
    author_email = tg.__email__,
    description = tg.__summary__,
    license = tg.__license__,
    url = tg.__url__,
    download_url = 'http://python.org/pypi/%s' % tg.__package__,
    long_description = re.sub(r'(\.\.[\s]*[\w]*::[\s]*[\w+]*\n)+', r'::\n',
                              open('README.txt').read()),
    platforms = "OS Independent - Anywhere Python, Trac >=0.11 is known to run.",
    install_requires = ['Trac>=0.11'],
    keywords = "adsense trac",
    packages = ['tracext', 'tracext.google', 'tracext.google.search'],
    namespace_packages = ['tracext', 'tracext.google'],
    package_data = {'tracext.google.search': ['templates/*.html',
                                              'htdocs/*.css']},
    classifiers = ['Framework :: Trac'],
    entry_points = """
    [trac.plugins]
      tracext.google.search = tracext.google.search
      tracext.google.search.admin = tracext.google.search.admin
      tracext.google.search.search = tracext.google.search.search
    """
)
