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
from codereview.tests.util import prepare_comments, prepare_file_data
from trac.test import EnvironmentStub, Mock, MockPerm


class TestReviewCommentModel(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'codereview.model.*',
                                                             'codereview.peerreviewnew.*',
                                                             'codereview.peerreviewmain.*',
                                                             'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.req = Mock(href=Mock(), perm=MockPerm(), args={}, authname="Tester")
        prepare_file_data(self.env)
        prepare_comments(self.env)

    def tearDown(self):
        self.env.shutdown()

    def test_comments_by_file_id(self):
        # this is a dict, key: file_id as int, val: list of comment ids
        comments = ReviewCommentModel.comments_by_file_id(self.env)
        self.assertEqual(3, len(comments))
        self.assertEqual(2, len(comments[1]))
        self.assertEqual(3, len(comments[2]))
        self.assertEqual(2, len(comments[3]))

    def test_select_by_file_id_no_file(self):
        comments = list(ReviewCommentModel.select_by_file_id(self.env, 100))
        self.assertEqual(0, len(comments))

    def test_select_by_file_id_parent_comments(self):
        """Test with comment and additional comment tree"""
        # Note that this file has three comments. Two of them are part of a comment tree on line 13
        comments = list(ReviewCommentModel.select_by_file_id(self.env, 2))
        self.assertEqual(3, len(comments))

        lines = [c['line_num'] for c in comments]
        self.assertEqual(3, len(lines))
        # There're two comments on line 13
        res = {13: 0, 12: 0}
        for line in lines:
            res[line] += 1
        self.assertEqual(2, res[13])
        self.assertEqual(1, res[12])

    def test_select_by_file_id_comments(self):
        """Test with two comments on different lines."""
        # Note that this file has three comments. Two of them are part of a comment tree on line 13
        comments = list(ReviewCommentModel.select_by_file_id(self.env, 3))
        self.assertEqual(2, len(comments))

        lines = [c['line_num'] for c in comments]
        self.assertEqual(2, len(lines))
        res = {15: 0, 16: 0}
        for line in lines:
            res[line] += 1
        self.assertEqual(1, res[15])
        self.assertEqual(1, res[16])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestReviewCommentModel))
    return suite
