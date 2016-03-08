# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Model classes for objects persisted in the database."""

from trac.db import Column, Table

from utils import *


class TT_Template(object):
    """Represents a generated tt."""

    _schema = [
        Table('ticket_template_store')[
            Column('tt_time', type='int'),
            Column('tt_user'),
            Column('tt_name'),
            Column('tt_field'),
            Column('tt_value'),
        ]
    ]

    def __init__(self, env):
        """Initialize a new report with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env

    exists = property(fget=lambda self: self.id is not None,
                      doc="Whether this tt exists in the database")

    @classmethod
    def deleteCustom(cls, env, data):
        """Remove the tt from the database."""
        env.db_transaction("""
            DELETE FROM ticket_template_store
            WHERE tt_user=%s AND tt_name=%s
            """, (data['tt_user'], data['tt_name']))

    @classmethod
    def insert(cls, env, record):
        """Insert a new tt into the database."""
        env.db_transaction("""
            INSERT INTO ticket_template_store
              (tt_time,tt_user,tt_name,tt_field,tt_value)
            VALUES (%s,%s,%s,%s,%s)
            """, record)

    @classmethod
    def fetchCurrent(cls, env, data):
        """Retrieve an existing tt from the database by ID."""
        field_value_mapping = {}
        for tt_field, tt_value in env.db_query("""
                SELECT tt_field, tt_value FROM ticket_template_store
                WHERE tt_user=%s AND tt_time=(
                  SELECT max(tt_time)
                  FROM ticket_template_store
                  WHERE tt_name=%s)
                """, (data['tt_user'], data['tt_name'])):
            if tt_value:
                field_value_mapping[tt_field] = tt_value
        return field_value_mapping

    @classmethod
    def fetchAll(cls, env, data):
        """Retrieve an existing tt from the database by ID.
            result:
                {
                    "field_value_mapping":{
                            "default":{
                                    "summary":"aaa",
                                    "description":"bbb",
                                },

                        },
                    "field_value_mapping_custom":{
                            "my_template":{
                                    "summary":"ccc",
                                    "description":"ddd",
                                },

                        },
                }

        """

        real_user = data.get('tt_user')
        req_args = data.get('req_args')

        field_value_mapping = {}
        field_value_mapping_custom = {}
        for tt_name, tt_field, tt_value in env.db_query("""
                SELECT tt_name, tt_field, tt_value
                FROM ticket_template_store WHERE tt_user=%s
                """, (data['tt_user'],)):
            if tt_name not in field_value_mapping_custom:
                field_value_mapping_custom[tt_name] = {}
            if tt_value:
                tt_value = formatField(env.config, tt_value, real_user,
                                       req_args)
                field_value_mapping_custom[tt_name][tt_field] = tt_value

        # field_value_mapping
        tt_name_list = [name for name, in env.db_query("""
            SELECT DISTINCT tt_name FROM ticket_template_store
            WHERE tt_user=%s
            """, (SYSTEM_USER,))]

        data['tt_user'] = SYSTEM_USER
        for tt_name in tt_name_list:
            data['tt_name'] = tt_name

            for tt_field, tt_value in env.db_query("""
                    SELECT tt_field, tt_value FROM ticket_template_store
                    WHERE tt_user=%s AND tt_name=%s
                      AND tt_time=(SELECT max(tt_time)
                        FROM ticket_template_store WHERE tt_name=%s)
                    """, (data['tt_user'], data['tt_name'], data['tt_name'])):
                if tt_name not in field_value_mapping:
                    field_value_mapping[tt_name] = {}
                if tt_value:
                    tt_value = formatField(env.config, tt_value, real_user,
                                           req_args)
                    field_value_mapping[tt_name][tt_field] = tt_value

        result = {
            'field_value_mapping': field_value_mapping,
            'field_value_mapping_custom': field_value_mapping_custom
        }
        return result

    @classmethod
    def getCustomTemplate(cls, env, tt_user):
        """Retrieve from the database that match
        the specified criteria.
        """
        return [name for name, in env.db_query("""
            SELECT DISTINCT tt_name FROM ticket_template_store
            WHERE tt_user=%s ORDER BY tt_name
            """, (tt_user,))]

    @classmethod
    def fetch(cls, env, tt_name):
        """Retrieve an existing tt from the database by ID."""
        tt_value = None
        for value, in env.db_query("""
                SELECT tt_value FROM ticket_template_store
                WHERE tt_time=(
                  SELECT max(tt_time)
                  FROM ticket_template_store
                  WHERE tt_name=%s)
                """, (tt_name,)):
            tt_value = value
        return tt_value

    @classmethod
    def fetchNames(cls, env):
        """fetch a list of existing tt names from database"""
        return [name for name, in env.db_query("""
            SELECT DISTINCT tt_name FROM ticket_template_store
            """)]


schema = TT_Template._schema
schema_version = 4
