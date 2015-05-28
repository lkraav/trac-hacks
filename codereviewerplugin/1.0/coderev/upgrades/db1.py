# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.db import Table, Column, Index

from coderev.compat import DatabaseManager


def do_upgrade(env, ver, cursor):

    schema = [
        Table('codereviewer')[
            Column('repo', type='text'),
            Column('changeset', type='text'),
            Column('status', type='text'),
            Column('reviewer', type='text'),
            Column('summary', type='text'),
            Column('time', type='integer'),
            Index(['repo', 'changeset', 'time']),
        ],
    ]

    DatabaseManager(env).create_tables(schema)
