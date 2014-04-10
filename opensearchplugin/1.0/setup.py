#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup, find_packages

version = '0.2'

setup(
    name='OpenSearch',
    version=version,
    classifiers=['Development Status :: 4 - Beta',
                 'Framework :: Trac'],
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/matobaa',
    description='Provides Federated search via Windows Explorer, Internet Explorer, Office IME 2010 search and so on.',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={'opensearch': ['templates/**']},
    entry_points={
        'trac.plugins': [
            'OpenSearch = opensearch.handler',
        ]
    },
)
