#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.

from setuptools import setup, find_packages

PACKAGE = 'Traclate'
VERSION = '0.1'

extra = {}
try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py',                'trac.dist:extract_python', None),
            ('**/templates/**.html', 'genshi', None)
        ]
        extra['message_extractors'] = {
            'traclate': extractors,
        }
except ImportError:
    pass

setup(
    name = PACKAGE,
    version = VERSION,
    description = 'Plugin for software translation',
    author = "Dirk Stöcker",
    author_email = "trac@dstoecker.de",
    url = 'http://trac-hacks.org/wiki/Traclate',
    download_url = 'http://trac-hacks.org/wiki/Traclate',
    license = 'BSD',
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License', 
    ],
    keywords='trac plugin',
    packages = find_packages(),
    package_data = {'traclate': ['templates/*', 'htdocs/*', 'locale/*/LC_MESSAGES/*.mo']},
    install_requires = ['Trac >= 1.0'],
    extras_require = {
        'json': ['python>=2.6']
    },
    entry_points = """
        [trac.plugins]
        traclate = traclate.web
        traclate.admin = traclate.admin
    """,
    zip_safe = False,
    **extra
)
