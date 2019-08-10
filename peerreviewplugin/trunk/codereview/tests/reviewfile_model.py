# -*- coding: utf-8 -*-

import unittest
from collections import defaultdict
from trac.test import EnvironmentStub, Mock, MockPerm
from codereview.model import  PeerReviewModel, ReviewFileModel, PeerReviewModelProvider
from codereview.peerReviewCommentCallback import PeerReviewCommentHandler
from codereview.peerReviewPerform import get_parent_file_id


__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


def _prepare_file_data(env):
    # review_id, path, start, end, revision, status
    files = [
        [1, '/foo/bar', 5, 100, '1234', 'new', None],
        [1, '/foo/bar2', 6, 101, '1234', 'new', None],
        [2, '/foo/bar', 5, 100, '1234', 'new', None],
        [2, '/foo/bar2', 6, 101, '12346', 'new', None],
        [2, '/foo/bar3', 7, 102, '12347', 'new', None],
        [3, '/foo/bar2', 6, 101, '1234', 'new', None],
        [4, '/foo/bar', 5, 100, '1234', 'new', None],
        [4, '/foo/bar2', 6, 101, '1234', 'new', None],
        # File list data for several projects
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjFoo'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjFoo'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBar'],
        [0, '/foo/bar2', 6, 101, '12346', 'new', 'PrjBar'],
        [0, '/foo/bar3', 7, 102, '12347', 'new', 'PrjFoo'],
        [0, '/foo/bar/baz', 6, 101, '1234', 'new', 'PrjBar'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBaz'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjBaz'],
    ]
    for f in files:
        rfm = ReviewFileModel(env)
        rfm['review_id'] = f[0]
        rfm['path'] = f[1]
        rfm['line_start'] = f[2]
        rfm['line_end'] = f[3]
        rfm['revision'] = f[4]
        rfm['status'] = f[5]
        rfm['project'] = f[6]
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

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*', 'codereview.*'])
        PeerReviewModelProvider(self.env).environment_created()
        _prepare_file_data(self.env)
        _prepare_review_data(self.env)
        self.plugin = PeerReviewCommentHandler(self.env)
        self.req = Mock(href=Mock(), perm=MockPerm())
        self.req.authname = 'tester'

    def tearDown(self):
        self.env.shutdown()

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

    def test_file_dict_by_review(self):
        fdict = ReviewFileModel.file_dict_by_review(self.env)
        self.assertEqual(4, len(fdict))
        for k, val in fdict.items():
            self.assertIsInstance(k, int)
            for item in val:
                self.assertIsInstance(item, ReviewFileModel)
        # Check number of files for the given review fdict[x]
        self.assertEqual(2, len(fdict[1]))
        self.assertEqual(3, len(fdict[2]))
        self.assertEqual(1, len(fdict[3]))
        self.assertEqual(2, len(fdict[4]))
        # We don't check every file here...
        self.assertEqual('/foo/bar', fdict[1][0]['path'])
        self.assertEqual('1234', fdict[1][0]['revision'])
        self.assertEqual('/foo/bar2', fdict[1][1]['path'])

    def test_select_by_review(self):
        files = list(ReviewFileModel.select_by_review(self.env, 2))
        self.assertEqual(3, len(files))
        fdata = {'/foo/bar': [5, 100, '1234', 'new'],
                 '/foo/bar2': [6, 101, '12346', 'new'],
                 '/foo/bar3': [7, 102, '12347', 'new']}
        for file_ in files:
            self.assertEqual(fdata[file_['path']][2], file_['revision'])
            self.assertEqual(fdata[file_['path']][0], file_['line_start'])

    def test_delete_files_by_project_name(self):
        files = list(ReviewFileModel.select_by_review(self.env, 0))
        self.assertEqual(8, len(files))
        ReviewFileModel.delete_files_by_project_name(self.env, 'PrjFoo')
        files = list(ReviewFileModel.select_by_review(self.env, 0))
        self.assertEqual(5, len(files))
        fdict = defaultdict(list)
        # Make dict with key: project name, val: list of file objects
        for file_ in files:
            fdict[file_['project']].append(file_)
        self.assertEqual(3, len(fdict['PrjBar']))
        self.assertEqual(2, len(fdict['PrjBaz']))


def reviewfile_model_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestReviewFileModel))

    return suite
