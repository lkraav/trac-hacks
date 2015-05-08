# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Gefasoft AG
# Copyright (C) 2015 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup
# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='Transmanager',
    version='0.1.2',
    author='Gefasoft AG, Barbara Streppel, Franz Mayer',
    description='Plugin for managing translation files',
    url='http://www.gefasoft-muenchen.de',
    download_url='http://trac-hacks.org/wiki/TranslationManagerPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points={"trac.plugins": [
            "transmgr.main = transmgr.main",
    ]
    },
    package_data={'transmgr': [
        'htdocs/css/*.css',
        'htdocs/js/*.js',
        'templates/*.html',
        'templates/*.txt',
    ]}
)
