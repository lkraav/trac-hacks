#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup, find_packages

version = '0.1'

setup(
    name='AutoPagerize Enabler',
    version=version,
    classifiers=['Development Status :: 4 - Beta',
                 'Framework :: Trac'],
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='Enables autoPagerize on Trac; see http://autopagerize.net/',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    entry_points={
        'trac.plugins': [
            'AutoPagerize = autopagerize.enabler',
        ]
    },
)
