# -*- coding: utf-8 -*-

import unittest
from codereview.model import ReviewCommentModel, PeerReviewModel, ReviewFileModel, PeerReviewModelProvider
from codereview.peerReviewCommentCallback import PeerReviewCommentHandler
from datetime import datetime
from trac.admin.console import TracAdmin
from trac.perm import PermissionError
from trac.test import EnvironmentStub, Mock, MockPerm, MockRequest
from trac.util.datefmt import to_datetime, to_utimestamp


__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


# reviewer (name), review_id
names = (['user1', 3], ['user2', 3], ['user3', 3],
         ['user4', 4], ['user5', 4],
         ['user4', 2], ['user5', 2],
         ['user2', 1], ['user3', 1], ['user4', 1], ['user5', 1])


def _prepare_review_data(env):
    # owner, status, created, name, notes, parent_id
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


def _prepare_file_data(env):
    # review_id, path, start, end, revision, status
    files = [
        [1, '/foo/bar', 5, 100, '1234', 'new'],
        [1, '/foo/bar2', 6, 101, '1234', 'new'],
        [2, '/foo/bar', 5, 100, '1234', 'new'],
        [2, '/foo/bar2', 6, 101, '1234', 'new'],
        [3, '/foo/bar', 5, 100, '1234', 'new'],
        [3, '/foo/bar2', 6, 101, '1234', 'new'],
        [4, '/foo/bar', 5, 100, '1234', 'new'],
        [4, '/foo/bar2', 6, 101, '1234', 'new'],
    ]
    for f in files:
        rfm = ReviewFileModel(env)
        rfm['review_id'] = f[0]
        rfm['path'] = f[1]
        rfm['line_start'] = f[2]
        rfm['line_end'] = f[3]
        rfm['revision'] = f[4]
        rfm['status'] = f[5]
        rfm.insert()


def _prepare_comment_data(env):
    pass


class TestCommentHelper(unittest.TestCase):

    def _add_permissions(self, env):
        admin = TracAdmin()
        admin.env_set('Testenv', env)
        admin.onecmd("permission add Tester TICKET_VIEW")  # User not allowed to perform code reviews
        admin.onecmd("permission add Rev1 TRAC_ADMIN")  # This one is also an allowed user
        admin.onecmd("permission add Rev2 TICKET_VIEW")
        admin.onecmd("permission add Rev3 TICKET_VIEW")
        admin.onecmd("permission add Rev1 RevGroup")
        admin.onecmd("permission add Rev2 RevGroup")
        for item in set([usr[0] for usr in names]):
            admin.onecmd("permission add %s CODE_REVIEW_DEV" % item)

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                              'codereview.model.*',
                                                              'codereview.peerreviewnew.*',
                                                              'codereview.peerreviewmain.*',
                                                              'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        _prepare_file_data(self.env)
        _prepare_review_data(self.env)
        _prepare_comment_data(self.env)
        self.plugin = PeerReviewCommentHandler(self.env)
        self.req = Mock(href=Mock(), perm=MockPerm())
        self.req.authname = 'tester'

    def tearDown(self):
        self.env.shutdown()

    def test_review_is_closed(self):
        self.req.args = {
            'IDFile': 1
        }
        self.assertFalse(self.plugin.review_is_closed(self.req))
        self.req.args = {
            'IDFile': 4
        }
        self.assertTrue(self.plugin.review_is_closed(self.req))
        self.req.args = {
            'IDFile': 7
        }
        self.assertFalse(self.plugin.review_is_closed(self.req))

    def test_get_comment_tree(self):
        """Only checks if the correct review is selected from the file id."""
        # There is no test for correct comment tree atm.
        self.req.args = {
            'IDFile': 3
        }
        data = {}
        self.plugin.get_comment_tree(self.req, data)
        self.assertIsNone(data.get('fileID'))
        self.assertIsNone(data.get('review'))

        self.req.args['LineNum'] = 2
        self.plugin.get_comment_tree(self.req, data)
        self.assertTrue(isinstance(data.get('review'), PeerReviewModel))
        self.assertEqual(2, data.get('review')['review_id'])

    def test_process_request_addcomment(self):
        self._add_permissions(self.env)
        # User Rev1 has TRAC_ADMIN so the user is for sure allowed to add a comment. Otherwise
        # the request may be rejected.
        # Insert two comments here
        req = MockRequest(self.env, href=Mock(), authname='Rev1', method='POST',
                          args={'addcomment': "1",
                                'fileid': '1',
                                'comment': "The comment text",
                                'line': '123',
                                'parentid': -1})
        self.assertIsNone(self.plugin.process_request(req))
        req = MockRequest(self.env, href=Mock(), authname='Rev1', method='POST',
                          args={'addcomment': "1",
                                'fileid': '1',
                                'comment': "The comment text 2",
                                'line': '124',
                                'parentid': '1'})
        self.assertIsNone(self.plugin.process_request(req))
        # Check results.
        comments = ReviewCommentModel.comments_by_file_id(self.env)
        self.assertEqual(2, len(comments[1]))  # comments is a dict but the keys are ints, val: list of comment ids
        for row in self.env.db_query("SELECT * FROM peerreviewcomment"):
            self.assertEqual(1, row[1])
            self.assertEqual(u'Rev1', row[4])
            if row[0] == 1:
                self.assertEqual(-1, row[2])
                self.assertEqual(123, row[3])
                self.assertEqual(u"The comment text", row[5])
            else:
                self.assertEqual(1, row[2])
                self.assertEqual(124, row[3])
                self.assertEqual(u"The comment text 2", row[5])

    def test_process_request_no_perm(self):
        req = MockRequest(self.env, href=Mock(), authname='user1')
        self.assertRaises(PermissionError, self.plugin.process_request, req)


def comment_callback_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestCommentHelper))

    return suite
