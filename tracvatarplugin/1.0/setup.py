#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
import os
import re

from setuptools import setup

v = open(os.path.join(os.path.dirname(__file__), 'tracvatar', '__init__.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
v.close()

setup(
    name = 'tracvatar',
    version = VERSION,
    packages = ['tracvatar'],
    package_data = {'tracvatar': ['htdocs/*.js', 'htdocs/*.css']},

    author = 'Mike Bayer',
    author_email = 'mike_mp@zzzcomputing.com',
    description = 'Add gravatar icons to various points around trac',
    long_description = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    license = 'BSD',
    keywords = 'trac plugin gravatar',
    url = 'http://bitbucket.org/zzzeek/tracvatar',
    classifiers = [
        'Framework :: Trac',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    install_requires = ['Trac'],

    entry_points = {
        'trac.plugins': [
            'tracvatar.web_ui = tracvatar.web_ui',
        ],
    },
)


