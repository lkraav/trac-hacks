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
from codereview.model import PeerReviewModelProvider
from codereview.peerReviewPerform import CommentAnnotator
from codereview.tests.util import prepare_comments, prepare_file_data, prepare_review_data
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock, MockPerm, MockRequest


class TestCommentAnnotator(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                              'codereview.model.*',
                                                              'codereview.peerreviewnew.*',
                                                              'codereview.peerreviewmain.*',
                                                              'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.req = Mock(href=Mock(), perm=MockPerm(), args={}, authname="Tester")
        prepare_file_data(self.env)
        prepare_review_data(self.env)
        prepare_comments(self.env)

    def tearDown(self):
        self.env.shutdown()

    def test_prep_peer(self):
        # Note that this isn't testing all the permission or locked state variations yet.
        # Because of the Mock* objects quite a few checks end with 'allowed'
        # The method prep_peer() is indirectly tested by creating the CommentAnnotator object
        # Note that this file has three comments. Two of them are part of a comment tree on line 13
        resource = Resource('peerreviewfile', 2)
        context = Mock(req=MockRequest(self.env), resource=resource)
        annotator = CommentAnnotator(self.env, context, 'path/file.png')
        data = annotator.data
        # annotator.data: [list of comment ids, PeerReviewModel, locked]
        # The review is the one this file is associated with
        self.assertEqual(3, len(data))
        self.assertEqual(1, data[1]['review_id'])
        self.assertFalse(data[2])
        # Now check for correct comments
        self.assertEqual(3, len(data[0]))  # number of comment lines
        # There're two comments on line 13
        res = {13: 0, 12: 0}
        for line in data[0]:
            res[line] += 1
        self.assertEqual(2, res[13])
        self.assertEqual(1, res[12])

        # File for a locked review (closed)
        # Note that the finishing states are defined in one of the loaded plugins
        resource = Resource('peerreviewfile', 3)
        context = Mock(req=MockRequest(self.env), resource=resource)
        annotator = CommentAnnotator(self.env, context, 'path/file.png')
        data = annotator.data
        # annotator.data: [list of comment ids, PeerReviewModel, locked]
        # The review is the one this file is associated with
        self.assertEqual(3, len(annotator.data))
        self.assertEqual(2, annotator.data[1]['review_id'])
        self.assertTrue(annotator.data[2])
        # Check comments
        self.assertEqual(2, len(annotator.data[0]))  # number of comments
        res = {15: 0, 16: 0}
        for line in data[0]:
            res[line] += 1
        self.assertEqual(1, res[15])
        self.assertEqual(1, res[16])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommentAnnotator))
    return suite
