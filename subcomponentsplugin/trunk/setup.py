#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'TracSubcomponents',
    version = '0.0.1',
    packages = ['subcomponents'],
    package_data = { 'subcomponents': ['templates/*.html', 'htdocs/*.js', 'htdocs/*.css' ] },

    author = 'Niels Sascha Reedijk',
    author_email = 'niels.reedijk@gmail.com',
    description = 'Provides support for subcomponents in the interface.',
    license = 'BSD',
    keywords = 'trac plugin ticket query components',
    url = 'http://hg.haiku-os.org/trac-subcomponents',
    classifiers = [
        'Framework :: Trac',
        #'Development Status :: 1 - Planning',
        'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    
    install_requires = ['Trac>=0.11', 'Genshi>=0.5'],

    entry_points = {
        'trac.plugins': [
            'subcomponents.web_ui = subcomponents.web_ui',
        ]
    }
)
