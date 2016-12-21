#!/usr/bin/env python

from setuptools import setup

setup(
    name='ComponentHierarchy',
    version='1.2.0',
    packages=['componenthierarchy'],
    package_data={
        'componenthierarchy': [
            'htdocs/*.js',
            'htdocs/css/*.css',
        ]
    },
    author='thomasd',
    author_email='tdoering@baumer.com',
    maintainer='falkb',
    license="BSD 3-Clause",
    url='https://trac-hacks.org/wiki/ComponentHierarchyPlugin',
    description='ComponentHierarchy',
    long_description='ComponentHierarchy',
    keywords='ticket component hierarchy',
    install_requires=['Trac'],
    entry_points={'trac.plugins': ['componenthierarchy = componenthierarchy']}
)
