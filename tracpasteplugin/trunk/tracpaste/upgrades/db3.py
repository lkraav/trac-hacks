# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Armin Ronacher <armin.ronacher@active-4.com>
# Copyright (C) 2008 Michael Renzmann <mrenzmann@otaku42.de>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.db.api import DatabaseManager

from tracpaste.db import schema


def do_upgrade(env, ver, cursor):
    """Convert permission PASTEBIN_USE to PASTEBIN_VIEW and PASTEBIN_CREATE.

    Add indexes to the database schema.
    """

    with env.db_transaction as db:
        # Convert permissions.
        for user, in db("""
                SELECT username FROM permission WHERE action='PASTEBIN_USE'
                """):
            db("""INSERT INTO permission (username, action)
               VALUES (%s, 'PASTEBIN_VIEW')
               """, (user,))
            db("""INSERT INTO permission (username, action)
               VALUES (%s, 'PASTEBIN_CREATE')
               """, (user,))
            db("""DELETE FROM permission
               WHERE username=%s AND action='PASTEBIN_USE'
               """, (user,))

        # Migrate to new schema.
        db("""CREATE TEMPORARY TABLE pastes_old AS
           SELECT * FROM pastes
           """)
        db.drop_table('pastes')

        DatabaseManager(env).create_tables(schema)

        db("""INSERT INTO pastes (id,title,author,mimetype,data,time)
           SELECT id,title,author,mimetype,data,time
           FROM pastes_old
           """)
        db.drop_table('pastes_old')
