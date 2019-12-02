#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='TracFieldTooltip',
    version='0.8.5',
    license='Modified BSD',
    author='MATOBA Akihiro',
    author_email='matobaa+trac-hacks@gmail.com',
    url='http://trac-hacks.org/wiki/FieldTooltipPlugin',
    description='tooltip help for ticket fields',
    zip_safe=True,
    packages=find_packages(exclude=['*.tests']),
    package_data={
        'tracfieldtooltip': [
            'htdocs/*.js',
            'htdocs/*.css',
        ]
    },
    entry_points={'trac.plugins': ['TracFieldTooltip = tracfieldtooltip']},
    install_requires=['Trac>=1.0'],
    long_description='This trac plugin offers tooltip help for ticket fields.',
    classifiers=[
        'Framework :: Trac',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: JavaScript',
        'License :: OSI Approved :: BSD License',
    ],
)
