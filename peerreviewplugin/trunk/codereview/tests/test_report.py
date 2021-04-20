# -*- coding: utf-8 -*-
# Copyright (c) 2019-2021 Cinc
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
from codereview.report import PeerReviewReport
from trac.admin.console import TracAdmin
from trac.perm import PermissionError
from trac.test import EnvironmentStub, MockRequest
from trac.web.chrome import Chrome


class TestResource(unittest.TestCase):

    def _add_permissions(self):
        admin = TracAdmin()
        admin.env_set('Testenv', self.env)
        admin.onecmd("permission add Tester TICKET_VIEW")  # User not allowed to perform code reviews
        admin.onecmd("permission add Rev1 TRAC_ADMIN")  # This one is also an allowed user
        admin.onecmd("permission add RevMgr CODE_REVIEW_MGR")
        admin.onecmd("permission add RevDev CODE_REVIEW_DEV")
        admin.onecmd("permission add RevView CODE_REVIEW_VIEW")
        admin.onecmd("permission add Rev1 RevGroup")
        admin.onecmd("permission add Rev2 RevGroup")

    def _create_standard_reports(self):
        # title, description
        reports = [['title 1', 'Report description 1'],
                   ['title 2', 'Report description 2'],
                   ['title 3', 'Report description 3'],
                   ['title 4', 'Report description 4']
                   ]
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for item in reports:
                cursor.execute("INSERT INTO report (title, description) "
                               "VALUES (%s,%s)", item)

    def _create_codereview_reports(self):
        desc = """{{{
#!comment
codereview=1
}}}
"""
        # title, description
        reports = [['title 1', desc + 'Report description 1'],
                   ['title 2', desc + 'Report description 2'],
                   ['title 3', desc + 'Report description 3'],
                   ['title 4', desc + 'Report description 4']
                   ]
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for item in reports:
                cursor.execute("INSERT INTO report (title, description) "
                               "VALUES (%s,%s)", item)

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                              'codereview.model.*',
                                                              'codereview.peerreviewnew.*',
                                                              'codereview.peerreviewmain.*',
                                                              'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.plugin = PeerReviewReport(self.env)
        self._add_permissions()
        # authname causes the addition of an empty permission cache.
        self.req = MockRequest(self.env, authname='user')

    def tearDown(self):
        self.env.shutdown()

    def test_get_active_navigation_item(self):
        self.assertEqual('peerReviewMain', self.plugin.get_active_navigation_item(self.req))

    def test_get_navigation_items(self):
        self.assertIsNone(self.plugin.get_navigation_items(self.req))

    def test_match_request(self):
        req = MockRequest(self.env, path_info="/peerreviewreport")
        self.assertTrue(self.plugin.match_request(req))
        req = MockRequest(self.env, path_info="/peerreviewreport/")
        self.assertFalse(self.plugin.match_request(req))

    def test_process_request_no_perm(self):
        self.assertRaises(PermissionError, self.plugin.process_request, self.req)

    def test_process_request_perm_view(self):
        """Test permission CODE_REVIEW_VIEW"""
        req = MockRequest(self.env, authname='RevView')
        self.assertRaises(PermissionError, self.plugin.process_request, req)

    def test_process_request_perm_dev(self):
        """Test permission CODE_REVIEW_DEV"""
        req = MockRequest(self.env, authname='RevDev')
        self.plugin.process_request(req)

    def test_process_request_perm_view_(self):
        """Test permission CODE_REVIEW_MGR"""
        req = MockRequest(self.env, authname='RevMgr')
        self.plugin.process_request(req)

    def test_process_request_reports_not_codereview(self):
        """Test with only non codereview reports"""
        req = MockRequest(self.env, authname='RevDev')
        self._create_standard_reports()
        res = self.plugin.process_request(req)
        if hasattr(Chrome, 'jenv'):
            self.assertEqual('peerreview_report_jinja.html', res[0])
            self.assertEqual(2, len(res))
        else:
            self.assertEqual('peerreview_report.html', res[0])
            self.assertIsNone(res[2])
        self.assertIn('reports', res[1])
        self.assertEqual(0, len(res[1]['reports']))

    def test_process_request_reports_codereview(self):
        """Test with additional codereview reports"""
        req = MockRequest(self.env, authname='RevDev')
        self._create_standard_reports()
        self._create_codereview_reports()
        res = self.plugin.process_request(req)
        if hasattr(Chrome, 'jenv'):
            self.assertEqual('peerreview_report_jinja.html', res[0])
            self.assertEqual(2, len(res))
        else:
            self.assertEqual('peerreview_report.html', res[0])
            self.assertIsNone(res[2])
        self.assertIn('reports', res[1])
        self.assertEqual(4, len(res[1]['reports']))
        for item in res[1]['reports']:
            # item is a dict
            self.assertEqual(3, len(item))  # each item is: id, title, desc
            for key in ('id', 'title', 'desc'):
                self.assertIn(key, item)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestResource))
    return suite
