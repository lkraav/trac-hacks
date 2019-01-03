# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The TracTicketChainedFields Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

import time

from trac.db import Column, Index, Table


class TracTicketChainedFields_List(object):
    """Represents a table."""

    _schema = [
        Table('tcf_list', key='id')[
            Column('id', auto_increment=True),
            Column('tcf_define'),
            Column('tcf_time', type='int'),
            Index(['id'])
        ]
    ]

    @classmethod
    def insert(cls, env, tcf_define):
        """Insert a new col1 into the database."""
        tcf_time = int(time.time())
        env.db_transaction("""
                INSERT INTO tcf_list (tcf_define, tcf_time)
                VALUES (%s, %s)
                """, (tcf_define, tcf_time))

    @classmethod
    def get_tcf_define(cls, env):
        """Retrieve from the database that match
        the specified criteria.
        """
        for tcf_define, in env.db_query("""
                SELECT tcf_define FROM tcf_list
                ORDER BY tcf_time DESC LIMIT 1
                """):
            return tcf_define
        else:
            return ''


schema = TracTicketChainedFields_List._schema
schema_version = 1
