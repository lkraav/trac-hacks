# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The TracTweakUI Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
# ----------------------------------------------------------------------------

from trac.db import Table, Column


class TracTweakUIModel(object):
    """Represents a table."""

    _schema = [
        Table('tractweakui_list', key='id')[
            Column('id', auto_increment=True),
            Column('time', type='int'),
            Column('path_pattern'),
            Column('filter_name'),
            Column('tweak_script'),
        ]
    ]

    def __init__(self, env, tweak_script=None):
        """Initialize a new entry with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env

    @classmethod
    def del_path_pattern(cls, env, path_pattern):
        """Remove the path_pattern from the database."""
        env.db_transaction("""
            DELETE FROM tractweakui_list WHERE path_pattern=%s
            """, (path_pattern,))

    @classmethod
    def save_tweak_script(cls, env, path_pattern, filter_name, tweak_script):
        """Insert a new tweak_script into the database."""
        with env.db_transaction as db:
            db("""
                DELETE FROM tractweakui_list
                WHERE path_pattern = %s AND filter_name = %s
                """, (path_pattern, filter_name, ))
            db("""
                INSERT INTO tractweakui_list
                 (path_pattern, filter_name, tweak_script)
                VALUES (%s, %s,  %s)
                """, (path_pattern, filter_name, tweak_script,))

    @classmethod
    def insert_path_pattern(cls, env, path_pattern):
        """Insert a new path_pattern into the database."""
        env.db_transaction("""
            INSERT INTO tractweakui_list (path_pattern) VALUES (%s)
            """, (path_pattern, ))

    @classmethod
    def save_path_pattern(cls, env, path_pattern, path_pattern_orig):
        """Insert a new path_pattern into the database."""
        env.db_transactions("""
            UPDATE tractweakui_list SET path_pattern = %s
            WHERE path_pattern = %s
            """, (path_pattern, path_pattern_orig))

    @classmethod
    def get_tweak_script(cls, env, path_pattern, filter_name):
        """Retrieve from the database that match
        the specified criteria.
        """
        for result, in env.db_query("""
                SELECT tweak_script FROM tractweakui_list
                WHERE path_pattern = %s AND filter_name = %s
                """, (path_pattern, filter_name, )):
            return result
        else:
            return ''

    @classmethod
    def get_path_scripts(cls, env, path_pattern):
        """Retrieve from the database that match the specified criteria.
        """
        return [s for s, in env.db_query("""
                SELECT tweak_script
                FROM tractweakui_list WHERE path_pattern = %s
                """, (path_pattern,)) if s]

    @classmethod
    def get_path_patterns(cls, env):
        """Retrieve from the database that match the specified criteria.
        """
        return [m for m, in env.db_query("""
                SELECT DISTINCT path_pattern
                FROM tractweakui_list ORDER BY path_pattern
                """) if m]

    @classmethod
    def get_path_filters(cls, env, path_pattern):
        """Retrieve from the database that match the specified criteria.
        """
        return [m for m, in env.db_query("""
                SELECT filter_name FROM tractweakui_list
                WHERE path_pattern = %s ORDER BY filter_name
                """, (path_pattern,)) if m]


schema = TracTweakUIModel._schema
schema_version = 1
schema_version_key = 'tractweakui_version'
