# -*- coding: utf-8 -*-

import unittest
from trac.test import EnvironmentStub, Mock, MockPerm
from ..model import  PeerReviewModel, ReviewFileModel, PeerReviewModelProvider
from ..peerReviewCommentCallback import PeerReviewCommentHandler

__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


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


def _prepare_review_data(env):
    # name, status
    revs = [
        ['name1', 'new'],
        ['name2', 'closed'],
        ['name3', 'new'],
        ['name4', 'foo']
    ]
    for rev in revs:
        r = PeerReviewModel(env)
        r['name'] = rev[0]
        r['status'] = rev[1]
        r.insert()


def _prepare_comment_data(env):
    pass


class TestCommentHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentStub(default_data=True, enable=['trac.*', 'codereview.*'])
        PeerReviewModelProvider(cls.env).environment_created()
        _prepare_file_data(cls.env)
        _prepare_review_data(cls.env)
        _prepare_comment_data(cls.env)
        cls.plugin = PeerReviewCommentHandler(cls.env)
        cls.req = Mock(href=Mock(), perm=MockPerm())
        cls.req.authname = 'tester'

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


def comment_callback_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestCommentHelper))

    return suite
