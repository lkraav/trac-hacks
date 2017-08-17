#!/usr/bin/env python
# -*- coding: utf-8 -*-

def main():
    kwargs = {
        'name': 'TracWysiwyg',
        'version': '0.12.0.7',
        'description': 'TracWiki WYSIWYG Editor',
        'license': 'BSD',
        'url': 'https://trac-hacks.org/wiki/TracWysiwygPlugin',
        'author': 'Jun Omae',
        'author_email': 'omae@opengroove.com',
        'packages': find_packages(exclude=['*.tests*']),
        'package_data': {
            'tracwysiwyg' : ['htdocs/*.js', 'htdocs/*.css', 'htdocs/*.png'],
        },
        'entry_points': {
            'trac.plugins': [
                'tracwysiwyg = tracwysiwyg',
            ],
        }
    }
    setup(**kwargs)

if __name__ == '__main__':
    from setuptools import setup, find_packages
    main()
