# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The TracTicketChangelogPlugin Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmmail.com>
#
# ----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

from trac.db import Table, Column, Index


class TicketlogStore(object):
    """Represents a table."""

    _schema = [
        Table('ticketlog_store', key='id')[
            Column('id', auto_increment=True),
            Column('col1'),
            Index(['col1'])
        ]
    ]

    def __init__(self, env, col1=None):
        """Initialize a new entry with the specified attributes.

        To actually create this build log in the database, the `insert`
        method needs to be called.
        """
        self.env = env
        self.col1 = col1

    @classmethod
    def delete(cls, env, col1):
        """Remove the col1 from the database."""
        env.db_transaction("""
            DELETE FROM ticketlog_store WHERE col1=%s
            """, (col1,))

    @classmethod
    def insert(cls, env, col1):
        """Insert a new col1 into the database."""

        with env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO ticketlog_store (col1, ) VALUES (%s,)
                """, (col1,))
            return db.get_last_id(cursor, 'ticketlog_store')

    @classmethod
    def get(cls, env):
        """Retrieve from the database that match
        the specified criteria.
        """
        return [col1 for col1, in env.db_query("""
                SELECT col1 FROM ticketlog_store ORDER BY col1
                """)]


schema = TicketlogStore._schema
schema_version = 1
