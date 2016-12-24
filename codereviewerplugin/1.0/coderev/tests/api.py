# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub

from coderev import api
from coderev.api import DB_NAME, DB_VERSION, CodeReviewerSystem
from coderev.compat import DatabaseManager
from coderev.upgrades import db1


class CodeReviewerSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()

    def tearDown(self):
        self._revert_schema_init()
        self.env.reset_db()

    def _revert_schema_init(self):
        with self.env.db_transaction as db:
            db("DROP TABLE IF EXISTS codereviewer")
            db("DROP TABLE IF EXISTS codereviewer_map")
            db("DELETE FROM system WHERE name='coderev'")

    def test_upgrade_environment_create(self):
        """Tables created in environment with no codereview installed."""
        dbm = DatabaseManager(self.env)
        db_init_ver = dbm.get_database_version(DB_NAME)

        CodeReviewerSystem(self.env).upgrade_environment()
        db_ver = dbm.get_database_version(DB_NAME)

        self.assertFalse(db_init_ver)
        self.assertEqual(DB_VERSION, db_ver)

    def test_upgrade_environment_upgrade(self):
        """Tables upgraded in environment with codereview installed at
        database version 1.
        """
        dbm = DatabaseManager(self.env)
        with self.env.db_transaction:
            db1.do_upgrade(self.env, 1, None)
            dbm.set_database_version(1, api.DB_NAME)

        db_init_ver = dbm.get_database_version(DB_NAME)
        CodeReviewerSystem(self.env).upgrade_environment()
        db_ver = dbm.get_database_version(DB_NAME)

        self.assertEqual(1, db_init_ver)
        self.assertEqual(DB_VERSION, db_ver)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeReviewerSystemTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
