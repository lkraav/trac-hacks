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
from trac.test import EnvironmentStub, Mock
from trac.web.chrome import Chrome
from trac.web.href import Href

from tracdiscussion.core import DiscussionCore


class DiscussionCoreTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()

        self.perms = PermissionSystem(self.env)

        self.core = DiscussionCore(self.env)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_match_request(self):
        path = '/discussion/%s'
        req = Mock(path_info='', args=dict())
        req.path_info = path % 'invalid/0'
        self.assertEqual(self.core.match_request(req), None)

        req.path_info = path % 'forum/1'
        self.assertTrue(self.core.match_request(req))
        req.path_info = path % 'topic/2'
        self.assertTrue(self.core.match_request(req))
        req.path_info = path % 'message/3'
        self.assertTrue(self.core.match_request(req))

    def test_nav_contributor(self):
        self.perms.grant_permission('anonymous', 'DISCUSSION_VIEW')
        req = Mock(abs_href=Href('http://example.org/trac.cgi'),
                   base_path='',
                   href=Href('/trac.cgi'), locale=None,
                   path_info='/discussion',
                   perm = PermissionCache(self.env),
                   add_redirect_listener=lambda listener: None
        )
        nav = Chrome(self.env).prepare_request(req)['nav']
        self.assertTrue([entry for entry in nav['mainnav']
                         if 'discussion' == entry['name']])

    def test_template_dirs_added(self):
        self.assertTrue(self.core in Chrome(self.env).template_providers)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionCoreTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
