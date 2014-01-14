#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Vladimir Abramov <kivsiak@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup


setup(
    name='TracTypedTicketWorkflow',
    version='0.2',
    packages=find_packages(),
    author='Vladimir Abramov',
    author_email='kivsiak@gmail.com',
    licence='BSD',
    description='Type - attribute workflow filter for trac ticket',
    long_description='Allow to filter actions by \'type\' ticket attribute',
    entry_points={
        'trac.plugins': [
            'typedworkflow.controller = typedworkflow.controller'
        ]
    },
)
