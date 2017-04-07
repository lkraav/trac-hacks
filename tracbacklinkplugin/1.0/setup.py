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
        'name': 'TracBackLinkPlugin',
        'version': '1.0.2',
        'description': 'Provide back links feature to Trac',
        'license': 'BSD',  # the same as Trac
        'url': 'https://trac-hacks.org/wiki/TracBackLinkPlugin',
        'author': 'OpenGroove,Inc.',
        'author_email': 'info@opengroove.com',
        'maintainer': 'Jun Omae',
        'maintainer_email': 'jun66j5@gmail.com',
        'packages': find_packages(exclude=['*.tests*']),
        'package_data': {
            'tracbacklink': [
                'locale/*.*', 'locale/*/LC_MESSAGES/*.mo',
            ],
        },
        'test_suite': 'tracbacklink.tests.test_suite',
        'install_requires': ['Trac'],
        'entry_points': {
            'trac.plugins': [
                'tracbacklink.api = tracbacklink.api',
                'tracbacklink.web_ui = tracbacklink.web_ui',
                'tracbacklink.admin = tracbacklink.admin',
            ],
        },
    }
    try:
        import babel
        del babel
        kwargs['message_extractors'] = {
            'tracbacklink': [
                ('**/*.py',              'python', None),
                ('**/templates/**.html', 'genshi', None),
            ],
        }
        from trac.util.dist import get_l10n_cmdclass
        kwargs['cmdclass'] = get_l10n_cmdclass()
    except ImportError:
        pass

    setup(**kwargs)

if __name__ == '__main__':
    main()
