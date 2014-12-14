#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import setup

setup(
    name='TracSelfDelete',
    version='2.0',
    packages=['selfdelete'],
    author="Noah Kantrowitz",
    author_email="noah@coderanger.net",
    description="Remove Trac wiki pages and attachments that you created.",
    long_description="Allows users to delete wiki pages and attachments that they created..",
    license="BSD",
    keywords="trac plugin wiki attachment delete",
    url="http://trac-hacks.org/wiki/SelfDeletePlugin",
    classifiers=[
        'Framework :: Trac',
    ],
    entry_points={
        'trac.plugins': [
            'selfdelete.filter = selfdelete.filter',
        ]
    }
)
