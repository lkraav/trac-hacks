# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012-2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import shutil
import tempfile
import unittest

from trac.db.api import DatabaseManager
from trac.db.schema import Column, Index, Table
from trac.perm import PermissionSystem
from trac.test import EnvironmentStub

from tracpaste.db import TracpasteSetup, schema_version, schema_version_name

schema_v1 = [
    Table('pastes', key='id')[
        Column('id', auto_increment=True),
        Column('title'),
        Column('author'),
        Column('mimetype'),
        Column('data'),
        Column('time', type='int'),
        Index(['id']),
        Index(['time'])
    ]
]


class TracpasteSetupTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracpaste.*'])
        self.env.path = tempfile.mkdtemp()
        self.dbm = DatabaseManager(self.env)
        self.tps = TracpasteSetup(self.env)

    def tearDown(self):
        with self.env.db_transaction as db:
            db.drop_table('pastes')
        self.env.reset_db()
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    def test_new_installation(self):
        self.tps.upgrade_environment()
        self.assertIn('pastes', self.dbm.get_table_names())
        self.assertEqual(schema_version,
                         self.dbm.get_database_version(schema_version_name))

    def test_upgrade_from_system_version_not_set(self):
        ps = PermissionSystem(self.env)
        self.dbm.create_tables(schema_v1)
        self.env.db_transaction("""
            INSERT INTO permission (username, action)
            VALUES (%s, 'PASTEBIN_USE')
            """, ('user1',))
        ps.grant_permission('user2', 'PASTEBIN_VIEW')

        self.tps.upgrade_environment()

        table_names = self.dbm.get_table_names()
        user1_perms = ps.get_user_permissions('user1')
        user2_perms = ps.get_user_permissions('user2')
        self.assertIn('pastes', table_names)
        self.assertNotIn('pastes_old', table_names)
        self.assertEqual(schema_version,
                         self.dbm.get_database_version(schema_version_name))
        self.assertIn('PASTEBIN_VIEW', user1_perms)
        self.assertIn('PASTEBIN_CREATE', user1_perms)
        self.assertNotIn('PASTEBIN_USE', user1_perms)
        self.assertIn('PASTEBIN_VIEW', user2_perms)
        self.assertNotIn('PASTEBIN_CREATE', user2_perms)
        self.assertNotIn('PASTEBIN_USE', user2_perms)

    def test_upgrade_from_system_version_1(self):
        ps = PermissionSystem(self.env)
        self.dbm.create_tables(schema_v1)
        self.dbm.set_database_version(1, schema_version_name)
        self.env.db_transaction("""
            INSERT INTO permission (username, action)
            VALUES (%s, 'PASTEBIN_USE')
            """, ('user1',))
        ps.grant_permission('user2', 'PASTEBIN_VIEW')

        self.tps.upgrade_environment()

        table_names = self.dbm.get_table_names()
        user1_perms = ps.get_user_permissions('user1')
        user2_perms = ps.get_user_permissions('user2')
        self.assertIn('pastes', table_names)
        self.assertNotIn('pastes_old', table_names)
        self.assertEqual(schema_version,
                         self.dbm.get_database_version(schema_version_name))
        self.assertIn('PASTEBIN_VIEW', user1_perms)
        self.assertIn('PASTEBIN_CREATE', user1_perms)
        self.assertNotIn('PASTEBIN_USE', user1_perms)
        self.assertIn('PASTEBIN_VIEW', user2_perms)
        self.assertNotIn('PASTEBIN_CREATE', user2_perms)
        self.assertNotIn('PASTEBIN_USE', user2_perms)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TracpasteSetupTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
