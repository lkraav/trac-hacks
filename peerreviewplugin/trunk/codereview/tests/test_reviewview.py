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
from codereview.model import PeerReviewModelProvider, ReviewFileModel
from codereview.peerReviewView import PeerReviewView
from codereview.tests.util import prepare_comments, prepare_file_data, prepare_review_data
from trac.test import EnvironmentStub, MockRequest

class TestPeerReviewView(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'codereview.model.*',
                                                             'codereview.peerreviewnew.*',
                                                             'codereview.peerreviewmain.*',
                                                             'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.plugin = PeerReviewView(self.env)
        self.req = MockRequest(self.env, path_info="/peerreviewview/1")
        prepare_review_data(self.env)
        prepare_file_data(self.env)
        prepare_comments(self.env)


    def tearDown(self):
        self.env.shutdown()

    def test_get_active_navigation_item(self):
        self.assertEqual('peerReviewMain', self.plugin.get_active_navigation_item(self.req))

    def test_get_navigation_items(self):
        self.assertEqual(0, len(self.plugin.get_navigation_items(self.req)))

    def test_match_request(self):
        paths = ("/peerreviewview/", "/peerreviewview",
                 "/peerreviewview/abc", "/peerreviewview/1a",
                 "/peerreviewview/a1")

        req = MockRequest(self.env, path_info="/peerreviewview/1")
        self.assertTrue(self.plugin.match_request(req))

        for path in paths:
            req = MockRequest(self.env, path_info=path)
            self.assertIsNone(self.plugin.match_request(req))

    def test_get_files_for_review_id_no_comments(self):
        req = MockRequest(self.env, authname='user1')
        review_id = 1
        files = self.plugin.get_files_for_review_id(req, review_id)
        self.assertIsInstance(files[0], ReviewFileModel)
        self.assertEqual(2, len(files))
        # Since we didn't want comment information the following attributes are not set
        try:
            foo = files[0].num_comments
            self.assertIsNone(foo)
        except AttributeError:
            pass
        try:
            foo = files[0].num_notread
            self.assertIsNone(foo)
        except AttributeError:
            pass

        # Another test with different number of associated files
        review_id = 2
        files = self.plugin.get_files_for_review_id(req, review_id)
        self.assertIsInstance(files[0], ReviewFileModel)
        self.assertEqual(3, len(files))

    def test_get_files_for_review_id_with_comments(self):
        req = MockRequest(self.env, authname='user1')
        review_id = 1
        files = self.plugin.get_files_for_review_id(req, review_id, True)
        self.assertIsInstance(files[0], ReviewFileModel)
        self.assertEqual(2, len(files))
        for item in files:
            if item['file_id'] == 1:
                self.assertEqual(2, item.num_comments)
                self.assertEqual(2, item.num_notread)
            else:
                self.assertEqual(3, item.num_comments)
                self.assertEqual(3, item.num_notread)

        review_id = 2
        files = self.plugin.get_files_for_review_id(req, review_id, True)
        self.assertIsInstance(files[0], ReviewFileModel)
        self.assertEqual(3, len(files))
        for item in files:
            if item['file_id'] == 3:
                self.assertEqual(2, item.num_comments)
                self.assertEqual(2, item.num_notread)
            else:
                self.assertEqual(0, item.num_comments)
                self.assertEqual(0, item.num_notread)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPeerReviewView))
    return suite
