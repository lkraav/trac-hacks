#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

def main():
    from setuptools import setup, find_packages

    kwargs = {
        'name': 'TracFlexibleQueryUiPlugin',
        'version': '1.0.0',
        'description': 'Make columns in custom query sortable and able to ' \
                       'add and remove columns without submiting form',
        'license': 'BSD',  # the same as Trac
        'url': 'https://trac-hacks.org/wiki/TracFlexibleQueryUiPlugin',
        'author': 'OpenGroove,Inc.',
        'author_email': 'info@opengroove.com',
        'maintainer': 'Jun Omae',
        'maintainer_email': 'jun66j5@gmail.com',
        'packages': find_packages(exclude=['*.tests*']),
        'package_data': {
            'tracflexiblequeryui': ['htdocs/*.js'],
        },
        'install_requires': ['Trac'],
        'entry_points': {
            'trac.plugins': [
                'tracflexiblequeryui.web_ui = tracflexiblequeryui.web_ui',
            ],
        },
    }
    setup(**kwargs)

if __name__ == '__main__':
    main()
