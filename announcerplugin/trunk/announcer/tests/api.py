# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac import __version__ as trac_version
from trac.db import Table, Column, Index
from trac.db.api import DatabaseManager
from trac.test import EnvironmentStub

from announcer import db_default
from announcer.api import AnnouncementSystem, AnnouncementEvent, \
                          SubscriptionResolver


class AnnouncementEventTestCase(unittest.TestCase):
    def setUp(self):
        self.event = AnnouncementEvent('realm', 'category', 'target')

    # Tests

    def test_init(self):
        # Examine properties of the initialized objekt.
        event = self.event
        event_props = [event.realm, event.category, event.target, event.author]
        self.assertEquals(event_props, ['realm', 'category', 'target', ''])

    def test_get_basic_terms(self):
        # Method doesn't accept any argument.
        self.assertRaises(TypeError, self.event.get_basic_terms, None)
        self.assertEquals(self.event.get_basic_terms(), ('realm', 'category'))

    def test_get_session_terms(self):
        # While having mandatory argument, return value is a constant.
        self.assertRaises(TypeError, self.event.get_session_terms)
        self.assertEquals(self.event.get_session_terms(None), tuple())
        self.assertEquals(self.event.get_session_terms('anonymous'), tuple())


class AnnouncementSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()
        self.an_sys = AnnouncementSystem(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _get_cursor_description(self, cursor):
        # Cursors don't look the same across Trac versions
        if trac_version < '0.12':
            return cursor.description
        else:
            return cursor.cursor.description

    def _schema_init(self, schema=None):
        # Current announcer schema is setup with enabled component anyway.
        #   Revert these changes for clean install testing.
        cursor = self.db.cursor()
        cursor.execute("DROP TABLE IF EXISTS subscriptions")
        cursor.execute("DROP TABLE IF EXISTS subscription")
        cursor.execute("DROP TABLE IF EXISTS subscription_attribute")
        cursor.execute("DELETE FROM system WHERE name='announcer_version'")

        if schema:
            connector = self.db_mgr._get_connector()[0]
            for table in schema:
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)

    def _verify_curr_schema(self):
        self.assertFalse(self.an_sys.environment_needs_upgrade(self.db))
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM subscription_attribute")
        columns = [col[0] for col in self._get_cursor_description(cursor)]
        self.assertTrue('name' not in columns)
        self.assertTrue('value' not in columns)
        self.assertEquals(
            ['id', 'sid', 'authenticated', 'class', 'realm', 'target'],
            columns
        )
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='announcer_version'
        """)
        version = int(cursor.fetchone()[0])
        self.assertEquals(db_default.schema_version, version)

    def _verify_version_unregistered(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='announcer_version'
        """)
        self.assertFalse(cursor.fetchone())

    # Tests

    def test_new_install(self):
        # Just do db table clean-up.
        self._schema_init()

        self.assertEquals(0, self.an_sys.get_schema_version(self.db))
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        self.an_sys.upgrade_environment(self.db)
        self._verify_curr_schema()

    def test_upgrade_to_schema_v2(self):
        # The initial db schema from r3015 - 10-Jan-2008 by Stephen Hansen.
        schema = [
            Table('subscriptions', key='id')[
                Column('id', auto_increment=True),
                Column('sid'),
                Column('enabled', type='int'),
                Column('managed', type='int'),
                Column('realm'),
                Column('category'),
                Column('rule'),
                Column('destination'),
                Column('format'),
                Index(['id']),
                Index(['realm', 'category', 'enabled']),
            ]
        ]
        self._schema_init(schema)

        # Populate tables with test data.
        cursor = self.db.cursor()
        cursor.executemany("""
            INSERT INTO session
                   (sid,authenticated,last_visit)
            VALUES (%s,%s,%s)
        """, (('somebody','0','0'), ('user','1','0')))
        cursor.executemany("""
            INSERT INTO session_attribute
                   (sid,authenticated,name,value)
            VALUES (%s,1,%s,%s)
        """, (('user','announcer_email_format_ticket','text/html'),
              ('user','announcer_specified_email','')))
        cursor.executemany("""
            INSERT INTO subscriptions
                   (sid,enabled,managed,
                    realm,category,rule,destination,format)
            VALUES (%s,%s,0,%s,%s,%s,%s,%s)
        """, (('somebody',1,'ticket','changed','1','1','email'),
              ('user',1,'ticket','attachment added','1','1','email')))

        self.assertEquals(1, self.an_sys.get_schema_version(self.db))
        target = 2
        db_default.schema_version = target
        self.assertTrue(self.an_sys.environment_needs_upgrade(self.db))

        # Change from r3047 - 13-Jan-2008 for announcer-0.2 by Stephen Hansen.
        # - 'subscriptions.destination', 'subscriptions.format'
        # + 'subscriptions.authenticated', 'subscriptions.transport'
        # 'subscriptions.managed' type='int' --> (default == char)
        self.an_sys.upgrade_environment(self.db)

        self.assertEquals(target, self.an_sys.get_schema_version(self.db))
        self._verify_version_unregistered()
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM subscriptions")
        columns = [col[0] for col in self._get_cursor_description(cursor)]
        self.assertEquals(['id', 'sid', 'authenticated', 'enabled', 'managed',
                           'realm', 'category', 'rule', 'transport'],
                          columns
        )


class SubscriptionResolverTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*'])
        self.env.path = tempfile.mkdtemp()
        self.db_mgr = DatabaseManager(self.env)
        self.db = self.env.get_db_cnx()

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_init(self):
        # Test just to confirm that SubscriptionResolver initializes cleanly
        #   and that setUp and tearDown both work.
        SubscriptionResolver(self.env)
        pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AnnouncementEventTestCase, 'test'))
    suite.addTest(unittest.makeSuite(AnnouncementSystemTestCase, 'test'))
    suite.addTest(unittest.makeSuite(SubscriptionResolverTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
