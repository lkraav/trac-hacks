# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#

import unittest
from trac.test import *
from ..model import PeerReviewModelProvider

__author__ = 'Cinc'
__copyright__ = "Copyright 2016-2021"
__license__ = "BSD"


class TestDbInitialUpgrade(unittest.TestCase):
    """Note that this only tests a clean install atm."""

    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentStub(enable=['trac.*', 'codereview.*'])

    @classmethod
    def tearDownClass(cls):
        cls.env.shutdown()

    def test_db_init(self):
        # Update database schema
        self.assertIsNone(PeerReviewModelProvider(self.env).environment_created())
        # Check for correct versions
        with self.env.db_query as db:
            cursor = db.cursor()
            tables = [
                ['peerreview_version', 6],
                ['peerreviewfile_version', 5],
                ['peerreviewcomment_version', 6],
                ['peerreviewer_version', 5],
                ['peerreviewdata_version', 3],
            ]
            for name, ver in tables:
                cursor.execute("select value FROM system WHERE name = %s", (name,))
                row = cursor.fetchone()
                self.assertEqual(ver, int(row[0]))
            # Check row len
        with self.env.db_transaction as db:
            table_len = [
                ['peerreview', 10],
                ['peerreviewfile', 11],
                ['peerreviewcomment', 11],
                ['peerreviewer', 5],
                ['peerreviewdata', 9],
            ]
            cursor = db.cursor()
            cursor.execute("INSERT INTO peerreview (owner) VALUES('tester'); ")
            cursor.execute("INSERT INTO peerreviewer (review_id) VALUES(1); ")
            cursor.execute("INSERT INTO peerreviewfile (path) VALUES('/foo/bar'); ")
            cursor.execute("INSERT INTO peerreviewcomment (author) VALUES('tester'); ")
            cursor.execute("INSERT INTO peerreviewdata (review_id) VALUES(1); ")
            for name, row_len in table_len:
                cursor.execute("SELECT * FROM %s " % name)
                row = cursor.fetchone()
                self.assertEqual(row_len, len(row))


def db_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestDbInitialUpgrade))

    return suite
