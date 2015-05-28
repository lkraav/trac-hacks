# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.db.api import DatabaseManager


def do_upgrade(env, ver, cursor):

    tables = [
        ('codereviewer', {'time': ('int', 'int64')}),
        ('codereviewer_map', {'time': ('int', 'int64')}),
    ]

    db_connector = DatabaseManager(env).get_connector()[0]
    for table, columns in tables:
        # Alter column types
        for sql in db_connector.alter_column_types(table, columns):
            cursor.execute(sql)
