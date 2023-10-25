#!/usr/bin/python3
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

NAME = 'TracIniAdminPanel'
PACKAGE = 'iniadminpanel'
VERSION = '1.6.0'

extra = {}
try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
except ImportError:
    pass

setup(
    name = NAME,
    version = VERSION,

    author = "Sebastian Krysmanski, Dirk Stöcker",
    author_email = 'trac@dstoecker.de',
    url = "https://trac-hacks.org/wiki/TracIniAdminPanelPlugin",
    description = "An admin panel for editing trac.ini",
    keywords = "trac plugin",
    license = "BSD",
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    install_requires = ['Trac>=1.5'],
    packages = find_packages(exclude=['*.texts*']),
    package_data = { PACKAGE: [ 'templates/*', 'htdocs/*', 'locale/*/LC_MESSAGES/*.mo' ] },

    entry_points = { 'trac.plugins': [
        '%s.web_ui = %s.web_ui' % (PACKAGE, PACKAGE),
        '%s.default_manager = %s.default_manager' % (PACKAGE, PACKAGE),
        # Add additional components here
    ] },
    **extra
)
