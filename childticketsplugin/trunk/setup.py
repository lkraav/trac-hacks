#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='TracChildTickets',
    version='2.6.0',
    packages=find_packages(),
    author='Mark Ryan',
    author_email='fatrascal@bigfoot.com@gmail.com',
    description='Provides support for pseudo child-tickets and a visual reference to these within a parent ticket.',
    keywords='trac plugins ticket dependency childtickets',
    url='https://trac-hacks.org/wiki/ChildTicketsPlugin',
    install_requires=[],
    entry_points={"trac.plugins": [
        "childtickets.web_ui = childtickets.web_ui",
        "childtickets.admin = childtickets.admin",
    ]},
    package_data={'childtickets': ['htdocs/css/*.css',
                                   'htdocs/js/*.js',
                                   'templates/*.html']},
)
