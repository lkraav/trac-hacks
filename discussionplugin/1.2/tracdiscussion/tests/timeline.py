# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2012-2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.perm import PermissionCache, PermissionSystem
from trac.test import EnvironmentStub, MockRequest

from tracdiscussion.timeline import DiscussionTimeline


class DiscussionTimelineTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        user = 'editor'
        self.req = MockRequest(self.env, authname=user)
        self.req.authname = user
        self.perms.grant_permission(user, 'DISCUSSION_VIEW')
        self.req.perm = PermissionCache(self.env, username=user)

        self.dt = DiscussionTimeline(self.env)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_get_timeline_filters(self):
        self.assertTrue(list(self.dt.get_timeline_filters(self.req)),
                        [('discussion', 'Discussion changes')])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionTimelineTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
