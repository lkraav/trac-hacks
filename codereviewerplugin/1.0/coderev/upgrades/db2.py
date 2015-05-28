# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.db import Table, Column

from coderev.compat import DatabaseManager


def do_upgrade(env, ver, cursor):

    schema = [
        Table('codereviewer_map', key=['repo', 'changeset', 'ticket'])[
            Column('repo', type='text'),
            Column('changeset', type='text'),
            Column('ticket', type='text'),
            Column('time', type='integer'),
        ],
    ]

    DatabaseManager(env).create_tables(schema)
