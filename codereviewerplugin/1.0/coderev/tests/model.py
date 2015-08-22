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


def _revert_schema_init(env):
    with env.db_transaction as db:
        db("DROP TABLE IF EXISTS codereviewer")
        db("DROP TABLE IF EXISTS codereviewer_map")
        db("DELETE FROM system WHERE name='coderev'")


class CodeReviewTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()

    def tearDown(self):
        _revert_schema_init(self.env)
        self.env.reset_db()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeReviewTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
