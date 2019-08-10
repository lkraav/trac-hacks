# -*- coding: utf-8 -*-
# Copyright (c) 2019 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest
from codereview.model import ReviewCommentModel, ReviewFileModel, PeerReviewModelProvider
from datetime import datetime
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.util.datefmt import to_datetime, to_utimestamp

def _prepare_file_data(env):
    # review_id, path, start, end, revision, status
    files = [
        [1, '/foo/bar', 5, 100, '1234', 'new', None, 'repo1'],
        [1, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        [2, '/foo/bar', 5, 100, '1234', 'closed', None, 'repo1'],
        [2, '/foo/bar2', 6, 101, '12346', 'closed', None, 'repo1'],
        [2, '/foo/bar3', 7, 102, '12347', 'closed', None, 'repo1'],
        [3, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        [4, '/foo/bar', 5, 100, '1234', 'new', None, 'repo1'],
        [4, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        # File list data for several projects
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar2', 6, 101, '12346', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar3', 7, 102, '12347', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar/baz', 6, 101, '1234', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBaz', 'repo1'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjBaz', 'repo1'],
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
        rfm['repo'] = f[7]
        rfm.insert()


def _prepare_comments(env):
    # file_id, parent_id, line_num, author, created, comment
    comments = [[1, -1, 123, 'user1', to_utimestamp(to_datetime(datetime(2019, 2, 4))), 'Comment 1'],
                [1, -1, 125, 'user4', to_utimestamp(to_datetime(datetime(2019, 2, 5))), 'Comment 2'],
                [2, -1, 12, 'user1', to_utimestamp(to_datetime(datetime(2019, 2, 5))), 'Comment 3'],
                [2, -1, 13, 'user2', to_utimestamp(to_datetime(datetime(2019, 2, 6))), 'Comment 4'],
                [2, -1, 14, 'user3', to_utimestamp(to_datetime(datetime(2019, 2, 7))), 'Comment 5'],
                [3, -1, 15, 'user3', to_utimestamp(to_datetime(datetime(2019, 2, 8))), 'Comment 6'],
                [3, -1, 16, 'user4', to_utimestamp(to_datetime(datetime(2019, 2, 9))), 'Comment 7'],
    ]
    with env.db_transaction as db:
        cursor = db.cursor()
        for comm in comments:
            cursor.execute("INSERT INTO peerreviewcomment (file_id, parent_id, line_num, author, created, comment) "
                           "VALUES (%s,%s,%s,%s,%s,%s)", comm)

class TestReviewCommentModel(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'codereview.model.*',
                                                             'codereview.peerreviewnew.*',
                                                             'codereview.peerreviewmain.*',
                                                             'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.req = Mock(href=Mock(), perm=MockPerm(), args={}, authname="Tester")
        _prepare_file_data(self.env)
        _prepare_comments(self.env)

    def tearDown(self):
        self.env.shutdown()

    def test_comments_by_file_id(self):
        # this is a dict, key: file_id as int, val: list of comment ids
        comments = ReviewCommentModel.comments_by_file_id(self.env)
        self.assertEqual(3, len(comments))
        self.assertEqual(2, len(comments[1]))
        self.assertEqual(3, len(comments[2]))
        self.assertEqual(2, len(comments[3]))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestReviewCommentModel))
    return suite
