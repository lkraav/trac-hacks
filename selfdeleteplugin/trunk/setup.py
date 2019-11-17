#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2014-2019 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracSelfDelete',
    version='2.1',
    packages=['selfdelete'],
    author="Ryan J Ollos",
    author_email="ryan.j.ollos@gmail.com",
    description="Permissions policy that allows users to delete wiki pages "
                "and attachments that they created.",
    license="BSD",
    keywords="trac plugin wiki attachment delete",
    url="https://trac-hacks.org/wiki/SelfDeletePlugin",
    classifiers=[
        'Framework :: Trac',
    ],
    entry_points={
        'trac.plugins': [
            'selfdelete.policy = selfdelete.policy',
        ]
    }
)
