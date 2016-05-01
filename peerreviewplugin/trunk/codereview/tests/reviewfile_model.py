# -*- coding: utf-8 -*-

import unittest
from trac.test import EnvironmentStub, Mock, MockPerm
from ..model import  PeerReviewModel, ReviewFileModel, PeerReviewModelProvider
from ..peerReviewCommentCallback import PeerReviewCommentHandler
from ..peerReviewPerform import get_parent_file_id


__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


def _prepare_file_data(env):
    # review_id, path, start, end, revision, status
    files = [
        [1, '/foo/bar', 5, 100, '1234', 'new'],
        [1, '/foo/bar2', 6, 101, '1234', 'new'],
        [2, '/foo/bar', 5, 100, '1234', 'new'],
        [2, '/foo/bar2', 6, 101, '12346', 'new'],
        [2, '/foo/bar3', 7, 102, '12347', 'new'],
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


class TestReviewFileModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentStub(default_data=True, enable=['trac.*', 'codereview.*'])
        PeerReviewModelProvider(cls.env).environment_created()
        _prepare_file_data(cls.env)
        _prepare_review_data(cls.env)
        cls.plugin = PeerReviewCommentHandler(cls.env)
        cls.req = Mock(href=Mock(), perm=MockPerm())
        cls.req.authname = 'tester'

    @classmethod
    def tearDownClass(cls):
        cls.env.shutdown()

    def test_get_parent_file_id(self):
        class RFile(object):
            pass

        rf_old = ReviewFileModel(self.env)
        rf_old['path'] = '/foo/bar'
        rf_old['line_start'] = 5
        rf_old['line_end'] = 100
        self.assertEqual(1, get_parent_file_id(self.env, rf_old, 1))
        self.assertEqual(3, get_parent_file_id(self.env, rf_old, 2))
        self.assertEqual(0, get_parent_file_id(self.env, rf_old, 3))
        self.assertEqual(7, get_parent_file_id(self.env, rf_old, 4))


def reviewfile_model_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestReviewFileModel))

    return suite
