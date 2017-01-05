#!/usr/bin/env python
#
# Copyright (C) 2016
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='MilestoneTemplatePlugin',
    description='Use templates when creating milestones.',
    long_description='Use templates when creating milestones.',
    version='0.1.2',
    url='http://trac-hacks.org/wiki/MilestoneTemplatePlugin',
    license="New BSD",
    author='Cinc-th',
    maintainer='Cinc-th',
    packages=['milestonetemplate'],
    package_data={
        'milestonetemplate': [
            'htdocs/js/*.js',
            'htdocs/css/*.css',
        ]},
    entry_points="""
        [trac.plugins]
        MilestoneTemplatePlugin = milestonetemplate.web_ui
    """,
)
