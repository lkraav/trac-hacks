# -*- coding: utf-8 -*-

import unittest
from trac.test import EnvironmentStub, Mock, MockPerm
from ..model import  PeerReviewModel, ReviewFile, ReviewFileModel, PeerReviewModelProvider
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

    def test_review_file_model(self):
        """Checks if new model gives same items as old model"""
        rf_obsolete = ReviewFile(self.env).select_by_review(self.env, 1)
        self.assertEqual(2, len(rf_obsolete))

        rf_obsolete = ReviewFile(self.env).select_by_review(self.env, 2)
        self.assertEqual(3, len(rf_obsolete))

        rf = list(ReviewFileModel(self.env).select_by_review(self.env, 2))
        self.assertEqual(3, len(rf))
        old = {}
        for item in rf_obsolete:
            old[item.path] = item
        new = {}
        for item in rf:
            new[item['path']] = item
        self.assertEqual(3, len(new))
        self.assertEqual(3, len(old))
        for item in rf_obsolete:
            p = item.path
            self.assertEqual(old[p].file_id, new[p]['file_id'])
            self.assertEqual(old[p].review_id, new[p]['review_id'])
            self.assertEqual(old[p].path, new[p]['path'])
            self.assertEqual(old[p].start, new[p]['line_start'])
            self.assertEqual(old[p].end, new[p]['line_end'])
            self.assertEqual(old[p].version, new[p]['revision'])

def reviewfile_model_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestReviewFileModel))

    return suite
