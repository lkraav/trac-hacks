#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name="MilestoneQuery",
    version='1.1.0',
    packages=find_packages(exclude=['*.tests']),
    author="Nic Ferrier",
    description="List milestones.",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    keywords="trac macro milestone",
    url="https://trac-hacks.org/wiki/MilestoneQueryMacro",
    install_requires=['Trac'],
    entry_points={
        "trac.plugins": [
            "MilestoneQuery = milestonequery.macro"
        ]
    }
)
