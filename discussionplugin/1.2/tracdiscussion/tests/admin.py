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

from trac.perm import PermissionCache, PermissionError, PermissionSystem
from trac.test import EnvironmentStub, MockRequest

from tracdiscussion.admin import DiscussionWebAdmin
from tracdiscussion.init import DiscussionInit


class DiscussionWebAdminTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        # Create admin user reference in the permission system.
        self.perms.grant_permission('admin', 'DISCUSSION_ADMIN')
        # Prepare a generic request object for admin actions.
        self.req = MockRequest(self.env, authname='admin', method='GET')
        self.req.perm = PermissionCache(self.env, 'admin')

        self.dwa = DiscussionWebAdmin(self.env)
        # Accomplish Discussion db schema setup.
        setup = DiscussionInit(self.env)
        setup.upgrade_environment()
        self.panel_template = dict(forum='admin-forum-list.html',
                                   group='admin-group-list.html')

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _assert_no_msg(self, req):
        self.assertEqual(req.chrome['notices'], [])
        self.assertEqual(req.chrome['warnings'], [])

    # Tests

    def test_render_admin_panel_no_perm(self):
        # Prepare anonymous request.
        req = MockRequest(self.env, authname='anonymous', method='GET')
        self.assertRaises(PermissionError, self.dwa.render_admin_panel,
                          req, 'discussion', 'forum', '')

    def test_render_forum_admin_panel(self):
        req = self.req
        response = self.dwa.render_admin_panel(req, 'discussion', 'forum', '')
        # Panel must use the appropriate template.
        self.assertEqual(response[0], self.panel_template['forum'])
        self._assert_no_msg(self.req)

    def test_render_group_admin_panel(self):
        req = self.req
        response = self.dwa.render_admin_panel(req, 'discussion', 'group', '')
        # Panel must use the appropriate template.
        self.assertEqual(response[0], self.panel_template['group'])
        self._assert_no_msg(self.req)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionWebAdminTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
