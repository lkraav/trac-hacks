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

    def test_create_environment(self):
        db_init_ver = DatabaseManager(self.env).get_database_version(DB_NAME)
        CodeReviewerSystem(self.env).environment_created()
        db_ver = DatabaseManager(self.env).get_database_version(DB_NAME)

        self.assertFalse(db_init_ver)
        self.assertEqual(DB_VERSION, db_ver)

    def test_upgrade_environment(self):
        api.DB_VERSION = 1
        CodeReviewerSystem(self.env).upgrade_environment()
        db_init_ver = DatabaseManager(self.env).get_database_version(DB_NAME)
        api.DB_VERSION = DB_VERSION
        CodeReviewerSystem(self.env).upgrade_environment()
        db_ver = DatabaseManager(self.env).get_database_version(DB_NAME)

        self.assertEqual(1, db_init_ver)
        self.assertEqual(DB_VERSION, db_ver)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeReviewerSystemTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
