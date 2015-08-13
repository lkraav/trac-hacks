# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.perm import PermissionCache, PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock

from tracdiscussion.ajax import DiscussionAjax
from tracdiscussion.init import DiscussionInit


class DiscussionAjaxTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        # Create user reference in the permission system.
        self.perms.grant_permission('user', 'DISCUSSION_VIEW')
        # Prepare a generic request object for view actions.
        self.req = Mock(authname='user', method='GET',
                   args=dict(), abs_href=self.env.abs_href,
                   chrome=dict(notices=[], warnings=[]),
                   href=self.env.abs_href, locale='',
                   redirect=lambda x: None, session=dict(), tz=''
        )
        self.req.perm = PermissionCache(self.env, 'user')

        self.da = DiscussionAjax(self.env)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _assert_no_msg(self, req):
        self.assertEqual(req.chrome['notices'], [])
        self.assertEqual(req.chrome['warnings'], [])

    # Tests

    def test_match_request(self):
        path = '/discussion/ajax/%s'
        req = Mock(path_info='', args=dict())
        req.path_info = path % 'invalid/0'
        self.assertEqual(self.da.match_request(req), None)

        req.path_info = path % 'forum/1'
        self.assertTrue(self.da.match_request(req))
        req.path_info = path % 'topic/2'
        self.assertTrue(self.da.match_request(req))
        req.path_info = path % 'message/3'
        self.assertTrue(self.da.match_request(req))

    def test_process_request(self):
        db = self.env.get_db_cnx()
        # Accomplish Discussion db schema setup.
        setup = DiscussionInit(self.env)
        setup.upgrade_environment(db)
        template = dict(forum='forum-list.html', topic='topic-list.html')

        req = self.req
        response = self.da.process_request(req)
        # Ajax handler must use the appropriate template.
        self.assertEqual(response[0], template['forum'])
        self._assert_no_msg(req)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionAjaxTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
