#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

setup(
    name='Tracchildtickettreemacro',
    version='1.1.1',
    packages=find_packages(),
    author='Mark Ryan',
    author_email='walnut.trac.hacks@gmail.com',
    description='Macro to see a complete tree/hierarchy of tickets under '
                'the given ticket number.',
    keywords='trac plugins ticket dependency childtickets',
    url='https://trac-hacks.org/wiki/ChildTicketTreeMacro',
    install_requires=['Trac'],
    entry_points={'trac.plugins': 'childtickettree = childtickettree'},
)
