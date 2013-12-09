#!/usr/bin/env python
#
# Copyright (C) 2009 ???
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='MultipleWorkflowPlugin',
    version='1.0',
    license="New BSD",
    packages=find_packages(exclude=['*.tests*']),
    entry_points="""
        [trac.plugins]
        MultipleWorkflowPlugin = multipleworkflow.workflow
    """,
)
