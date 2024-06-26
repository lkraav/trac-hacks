#!/usr/bin/env python
#
# Copyright (C) 2009/2015
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='MultipleWorkflowPlugin',
    description='Ticket workflows based on ticket type. Admin page for editing the workflows.',
    version='1.2.0',
    url='http://trac-hacks.org/wiki/MultipleWorkflowPlugin',
    license="New BSD",
    author='ermal',
    maintainer='Cinc-th',
    #packages=find_packages(exclude=['*.tests*']),
    packages=['multipleworkflow'],
    package_data={'multipleworkflow': ['templates/*', 'htdocs/js/*']},
    entry_points="""
        [trac.plugins]
        MultipleWorkflowPlugin = multipleworkflow.workflow
        MultipleWorkflowPAdminModule = multipleworkflow.web_ui
    """,
)
