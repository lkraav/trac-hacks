# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac import __version__ as trac_version
from trac.core import TracError
from trac.db import Table, Column, Index
from trac.db.api import DatabaseManager
from trac.test import EnvironmentStub

from tracdiscussion.init import DiscussionInit, schema_version

INSERT_VERSION_SQL = "INSERT INTO system (name, value) " \
                     "VALUES ('discussion_version', %s)"


class DiscussionInitTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)

    def tearDown(self):
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _check_schema(self):
        """Verify current schema by checking tables and their columns."""

        dburi = self.env.config.get('trac', 'database')
        with self.env.db_query as db:
            cursor = db.cursor()
            tables = self._get_tables(dburi)
            self.assertTrue('forum_group' in tables)
            cursor.execute("SELECT * FROM forum_group")
            self.assertEquals(
                ['id', 'name', 'description'],
                [col[0] for col in self._get_cursor_description(cursor)])

            self.assertTrue('forum' in tables)
            cursor.execute("SELECT * FROM forum")
            self.assertEquals(
                ['id', 'name', 'time', 'forum_group', 'author', 'moderators',
                 'subscribers', 'subject', 'description'],
                [col[0] for col in self._get_cursor_description(cursor)])

            self.assertTrue('topic' in tables)
            cursor.execute("SELECT * FROM topic")
            self.assertEquals(
                ['id', 'forum', 'time', 'author', 'subscribers', 'subject',
                 'body', 'status', 'priority'],
                [col[0] for col in self._get_cursor_description(cursor)])

            self.assertTrue('message' in tables)
            cursor.execute("SELECT * FROM message")
            messages = cursor.fetchall()
            self.assertEquals([], messages)
            self.assertEquals(
                ['id', 'forum', 'topic', 'replyto', 'time', 'author', 'body'],
                [col[0] for col in self._get_cursor_description(cursor)])

            cursor.execute("""
                SELECT value
                  FROM system
                 WHERE name='discussion_version'
            """)
            version = int(cursor.fetchone()[0])
            self.assertEquals(schema_version, version)

    def _get_tables(self, dburi):
        """Code from TracMigratePlugin by Jun Omae (see tracmigrate.admin)."""
        if dburi.startswith('sqlite:'):
            sql = """
                SELECT name
                  FROM sqlite_master
                 WHERE type='table'
                   AND NOT name='sqlite_sequence'
            """
        elif dburi.startswith('postgres:'):
            sql = """
                SELECT tablename
                  FROM pg_tables
                 WHERE schemaname = ANY (current_schemas(FALSE))
            """
        elif dburi.startswith('mysql:'):
            sql = "SHOW TABLES"
        else:
            raise TracError('Unsupported database type "%s"'
                            % dburi.split(':')[0])
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute(sql)
            return sorted(name for name, in cursor.fetchall())

    def _get_cursor_description(self, cursor):
        # Cursors don't look the same across Trac versions.
        if trac_version < '0.12':
            return cursor.description
        else:
            return cursor.cursor.description

    # Tests

    def test_new_install(self):
        setup = DiscussionInit(self.env)
        self.assertEquals(0, setup._get_schema_version())
        self.assertTrue(setup.environment_needs_upgrade())

        setup.upgrade_environment()
        self.assertFalse(setup.environment_needs_upgrade())
        self._check_schema()

    def test_upgrade_schema_v1(self):
        # Initial schema without 'forum_group' table.
        schema = [
            Table('forum', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('name'),
                Column('time', type='integer'),
                Column('moderators'),
                Column('subject'),
                Column('description')
            ],
            Table('topic', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('subject'),
                Column('body')
            ],
            Table('message', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('topic', type='integer'),
                Column('replyto', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('body')
            ]
        ]
        connector = self.db_mgr.get_connector()[0]
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in schema:
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)
            cursor.execute(INSERT_VERSION_SQL, '1')

        setup = DiscussionInit(self.env)
        self.assertEquals(1, setup._get_schema_version())
        self.assertTrue(setup.environment_needs_upgrade())

        setup.upgrade_environment()
        self.assertFalse(setup.environment_needs_upgrade())
        self._check_schema()

    def test_upgrade_schema_v2(self):
        # More recent schema with all tables, 'forum_group' and 'author'
        # columns added to 'forum' table.
        schema = [
            Table('forum_group', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('name'),
                Column('description')
            ],
            Table('forum', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('name'),
                Column('time', type='integer'),
                Column('forum_group', type='integer'),
                Column('author'),
                Column('moderators'),
                Column('subject'),
                Column('description')
            ],
            Table('topic', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('subject'),
                Column('body')
            ],
            Table('message', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('topic', type='integer'),
                Column('replyto', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('body')
            ]
        ]
        connector = self.db_mgr.get_connector()[0]
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in schema:
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)
            cursor.execute(INSERT_VERSION_SQL, '2')

        setup = DiscussionInit(self.env)
        self.assertEquals(2, setup._get_schema_version())
        self.assertTrue(setup.environment_needs_upgrade())

        setup.upgrade_environment()
        self.assertFalse(setup.environment_needs_upgrade())
        self._check_schema()

    def test_upgrade_schema_v3(self):
        # Schema version including 'subscribers' column in 'forum' table.
        schema = [
            Table('forum_group', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('name'),
                Column('description')
            ],
            Table('forum', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('name'),
                Column('time', type='integer'),
                Column('forum_group', type='integer'),
                Column('author'),
                Column('moderators'),
                Column('subscribers'),
                Column('subject'),
                Column('description')
            ],
            Table('topic', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('subscribers'),
                Column('subject'),
                Column('body')
            ],
            Table('message', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('topic', type='integer'),
                Column('replyto', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('body')
            ]
        ]
        connector = self.db_mgr.get_connector()[0]
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in schema:
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)
            cursor.execute(INSERT_VERSION_SQL, '3')

        setup = DiscussionInit(self.env)
        self.assertEquals(3, setup._get_schema_version())
        self.assertTrue(setup.environment_needs_upgrade())

        setup.upgrade_environment()
        self.assertFalse(setup.environment_needs_upgrade())
        self._check_schema()

    def test_upgrade_schema_v4(self):
        # Schema version including indices for forum, topic and message times.
        schema = [
            Table('forum_group', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('name'),
                Column('description')
            ],
            Table('forum', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('name'),
                Column('time', type='integer'),
                Column('forum_group', type='integer'),
                Column('author'),
                Column('moderators'),
                Column('subscribers'),
                Column('subject'),
                Column('description'),
                Index(['time'])
            ],
            Table('topic', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('subscribers'),
                Column('subject'),
                Column('body'),
                Index(['time'])
            ],
            Table('message', key='id')[
                Column('id', type='integer', auto_increment=True),
                Column('forum', type='integer'),
                Column('topic', type='integer'),
                Column('replyto', type='integer'),
                Column('time', type='integer'),
                Column('author'),
                Column('body'),
                Index(['time'])
            ]
        ]
        connector = self.db_mgr.get_connector()[0]
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in schema:
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)
            cursor.execute(INSERT_VERSION_SQL, '4')

        setup = DiscussionInit(self.env)
        self.assertEquals(4, setup._get_schema_version())
        self.assertTrue(setup.environment_needs_upgrade())

        setup.upgrade_environment()
        self.assertFalse(setup.environment_needs_upgrade())
        self._check_schema()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionInitTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
