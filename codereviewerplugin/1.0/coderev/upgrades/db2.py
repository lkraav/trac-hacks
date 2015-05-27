# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.db import Table, Column, Index, DatabaseManager

def do_upgrade(env, cursor):

    db_tables = [
        Table('codereviewer_map', key=['repo', 'changeset', 'ticket'])[
            Column('repo', type='text'),
            Column('changeset', type='text'),
            Column('ticket', type='text'),
            Column('time', type='integer'),
        ],
    ]

    # create the map table
    db_connector = DatabaseManager(env).get_connector()[0]
    for table in db_tables:
        for sql in db_connector.to_sql(table):
            cursor.execute(sql)
