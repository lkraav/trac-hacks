#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracHideVals',
    version='3.1',
    author='Noah Kantrowitz, Iker Jimenez',
    author_email='noah@coderanger.net, iker.jimenez@gmail.com',
    description='Hide ticket option values from certain users.',
    license='BSD',
    keywords='trac plugin',
    url='https://trac-hacks.org/wiki/HideValsPlugin',
    classifiers=[
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires=['Trac'],
    packages=['hidevals'],
    package_data={'hidevals': [
        'templates/*.html', 'htdocs/*.js', 'htdocs/*.css'
    ]},
    entry_points={
        'trac.plugins': [
            'hidevals.filter = hidevals.filter',
            'hidevals.api = hidevals.api',
            'hidevals.admin = hidevals.admin',
        ]
    },
)
