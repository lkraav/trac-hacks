# -*- coding: utf-8 -*-

import unittest
from datetime import datetime
from codereview.model import PeerReviewerModel, PeerReviewModelProvider
from trac.test import EnvironmentStub
from trac.util.datefmt import to_datetime, to_utimestamp


def _prepare_review_data(env):
    # owner, status, name, notes, parent_id
    revs = [
        ['Rev1', 'bar', to_utimestamp(to_datetime(datetime(2019, 2, 4))), 'name1', 'note1', 0],
        ['Rev1', 'closed', to_utimestamp(to_datetime(datetime(2019, 3, 4))), 'name2', 'note2', 0],
        ['Rev2', 'bar', to_utimestamp(to_datetime(datetime(2019, 3, 14))), 'name3', 'note3', 1],
        ['Rev3', 'foo', to_utimestamp(to_datetime(datetime(2019, 4, 4))), 'name4', 'note4', 2]
    ]

    with env.db_transaction as db:
        cursor = db.cursor()
        for rev in revs:
            cursor.execute("INSERT INTO peerreview (owner, status, created, name, notes, parent_id) "
                           "VALUES (%s,%s,%s,%s,%s,%s)", rev)


class TestPeerReviewerModel(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*', 'codereview.*'])
        PeerReviewModelProvider(self.env).environment_created()

    def tearDown(self):
        self.env.shutdown()

    def test_insert_delete(self):
        names = ('user1', 'user2', 'user3')
        for user in names:
            rev = PeerReviewerModel(self.env)
            rev['review_id'] = 3
            rev['reviewer'] = user
            rev['vote'] = -1
            rev.insert()
        rows = []
        for row in self.env.db_query("SELECT * FROM peerreviewer"):
            self.assertEqual(5, len(row))
            rows.append(row)
        self.assertEqual(3, len(rows))

        names2 = ('user4', 'user5')
        for user in names2:
            rev = PeerReviewerModel(self.env)
            rev['review_id'] = 4
            rev['reviewer'] = user
            rev['vote'] = -1
            rev.insert()
        users = []
        for row in self.env.db_query("SELECT * FROM peerreviewer"):
            self.assertEqual(5, len(row))
            users.append(row[2])
        self.assertEqual(5, len(users))
        # Check if different users are created
        for item in names + names2:
            self.assertIn(item, users)

        # Test deletion
        rev = PeerReviewerModel(self.env, 2)
        rev.delete()
        users = []
        for row in self.env.db_query("SELECT * FROM peerreviewer"):
            self.assertEqual(5, len(row))
            users.append(row[2])
        self.assertEqual(4, len(users))
        self.assertNotIn('user2', users)

    def test_select_by_review_id(self):
        # Preparation
        # reviewer (name), review_id
        names = (['user1', 3], ['user2', 3], ['user3', 3],
                 ['user4', 4], ['user5', 4])
        for user in names:
            rev = PeerReviewerModel(self.env)
            rev['review_id'] = user[1]
            rev['reviewer'] = user[0]
            rev['vote'] = -1
            rev.insert()
        users = []
        for row in self.env.db_query("SELECT * FROM peerreviewer"):
            self.assertEqual(5, len(row))
            users.append(row[2])
        self.assertEqual(5, len(users))

        # Test
        reviewers = list(PeerReviewerModel.select_by_review_id(self.env, 3))
        self.assertEqual(3, len(reviewers))
        for rev in reviewers:
            self.assertIn(rev['reviewer'], ('user1', 'user2', 'user3'))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPeerReviewerModel))
    return suite
