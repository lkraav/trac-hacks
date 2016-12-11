#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os

from setuptools import setup

extra = {}
try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py',                'trac.dist:extract_python', None),
            ('**/templates/**.html', 'genshi', None),
            ('**/templates/**.txt',  'genshi', {
                'template_class': 'genshi.template:TextTemplate'
            }),
        ]
        extra['message_extractors'] = {
            'themeengine': extractors,
        }
except ImportError:
    pass

setup(
    name = 'TracThemeEngine',
    version = '2.2.4',
    packages = ['themeengine'],
    package_data = { 'themeengine': ['templates/*.html', 'htdocs/*.js',
                                     'htdocs/*.css', 'htdocs/*.png',
                                     'htdocs/img/*.gif',
                                     'htdocs/farbtastic/*.png',
                                     'htdocs/farbtastic/*.js',
                                     'htdocs/farbtastic/*.css',
                                     # Ensure that locale folder is deployed
                                     'locale/README.txt',
                                     'locale/*/LC_MESSAGES/*.mo'] },
    author = 'Noah Kantrowitz',
    author_email = 'noah@coderanger.net',
    maintainer='Olemis Lang',
    maintainer_email='olemis+trac@gmail.com',
    description = 'Provide a modular interface to styling Trac',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license = '3-Clause BSD',
    keywords = 'trac plugin theme style',
    url = 'https://trac-hacks.org/wiki/ThemeEnginePlugin',
    download_url = 'https://trac-hacks.org/svn/themeengineplugin/0.11#egg=TracThemeEngine-dev',
    classifiers = [
        'Framework :: Trac',
        #'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    install_requires = ['Trac'],
    test_suite='themeengine.tests.test_suite',

    entry_points = {
        'trac.plugins': [
            'themeengine.web_ui = themeengine.web_ui',
            'themeengine.api = themeengine.api',
            'themeengine.admin = themeengine.admin',
        ],
    },
    **extra
)
