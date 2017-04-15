# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.perm import PermissionCache
from trac.test import MockRequest
from trac.web.chrome import Chrome
from trac.wiki.web_ui import WikiModule

from tracdiscussion.core import DiscussionCore
from tracdiscussion.tests.test import DiscussionBaseTestCase


class DiscussionCoreTestCase(DiscussionBaseTestCase):
    def setUp(self):
        DiscussionBaseTestCase.setUp(self)

        self.req = MockRequest(self.env, authname='reader')
        self.req.perm = PermissionCache(self.env, 'reader')

        self.core = DiscussionCore(self.env)

    # Tests

    def test_match_request(self):
        path = '/discussion/%s'
        req = MockRequest(self.env, path_info=path % 'invalid/0')
        self.assertEqual(self.core.match_request(req), None)

        req = MockRequest(self.env, path_info=path % 'forum/1')
        self.assertTrue(self.core.match_request(req))
        req = MockRequest(self.env, path_info=path % 'topic/2')
        self.assertTrue(self.core.match_request(req))
        req = MockRequest(self.env, path_info=path % 'message/3')
        self.assertTrue(self.core.match_request(req))

    def test_nav_contributor(self):
        self.perms.grant_permission('anonymous', 'DISCUSSION_VIEW')
        req = MockRequest(self.env, path_info='/discussion')
        nav = Chrome(self.env).prepare_request(req)['nav']
        self.assertTrue([entry for entry in nav['mainnav']
                         if 'discussion' == entry['name']])

    def test_search(self):
        results = [i for i in self.core.get_search_results(self.req,
                                                           ('hello',),
                                                           ('discussion',))]
        self.assertEqual(2, len(results))
        self.assertEqual(set(['Othello ;-)', 'Say "Hello world!"']),
                         set([result[-1] for result in results]))

    def test_template_dirs_added(self):
        self.assertTrue(self.core in Chrome(self.env).template_providers)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionCoreTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
