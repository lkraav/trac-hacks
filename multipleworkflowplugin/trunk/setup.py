#!/usr/bin/env python
#
# Copyright (C) 2009
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='MultipleWorkflowPlugin',
    description='Ticket workflows based on ticket type.',
    version='1.0',
    url='http://trac-hacks.org/wiki/MultipleWorkflowPlugin',
    license="New BSD",
    author='ermal',
    maintainer='Cinc-th',
    packages=find_packages(exclude=['*.tests*']),
    entry_points="""
        [trac.plugins]
        MultipleWorkflowPlugin = multipleworkflow.workflow
    """,
)
