#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='TracMultiSelectField',
    version='1.0.2',
    packages=['multiselectfield'],
    author='Olli Kallioinen',
    author_email='olli.kallioinen@iki.fi',
    description='A plugin providing a multiselection custom ticket field.',
    license='BSD',
    keywords='trac plugin multiselection',
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    package_data={
        'multiselectfield': [
            'htdocs/*.css',
            'htdocs/*.js',
            'htdocs/*.png'
        ]
    },
    entry_points={
        'trac.plugins': [
            'multiselectfield.filter = multiselectfield.filter',
        ]
    },
)
