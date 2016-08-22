#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2016 Edgewall Software
# Copyright (C) 2012 Ruth Trevor-Allen <fleeblewidget@gmail.com>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(name='MultiProjectCommitTicketUpdater',
      version='1.0.0',
      description='Multi-project version of commit_updater',
      author='fleeblewidget',
      author_email='fleeblewidget@gmail.com',
      license='3-Clause BSD',
      packages=['multicommitupdater'],
      entry_points = {
        'trac.plugins': [
            'multiprojectcommitticketupdater = multicommitupdater.commitupdater',
            ],
        },
      )
