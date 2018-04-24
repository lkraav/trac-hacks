#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name='TracHideVals',
    version='2.0',
    packages=['hidevals'],
    package_data={'hidevals': [
        'templates/*.html', 'htdocs/*.js', 'htdocs/*.css']},

    author='Noah Kantrowitz, Iker Jimenez',
    author_email='noah@coderanger.net, iker.jimenez@gmail.com',
    description='Hide ticket option values from certain users.',
    license='BSD',
    keywords='trac plugin',
    url='https://trac-hacks.org/wiki/HideValsPlugin',
    classifiers=[
        'Framework :: Trac',
    ],

    install_requires=['Trac'],

    entry_points={
        'trac.plugins': [
            'hidevals.filter = hidevals.filter',
            'hidevals.api = hidevals.api',
            'hidevals.admin = hidevals.admin',
        ]
    },
)
