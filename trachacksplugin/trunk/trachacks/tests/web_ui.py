# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.perm import PermissionCache, PermissionSystem
from trac.test import EnvironmentStub, MockRequest
from trac.web.api import RequestDone
from trac.web.main import RequestDispatcher
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

from trachacks.web_ui import ReadonlyHelpPolicy


class MockBoxMacro(WikiMacroBase):

    def expand_macro(self, formatter, name, content, args=None):
        return content

    def get_macros(self):
        yield 'box'


class ReadonlyHelpPolicyTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(
            enable=('trac.*', 'trachacks.web_ui.ReadonlyHelpPolicy',
                    MockBoxMacro))
        self.env.config.set('trac', 'permission_policies',
                            'ReadonlyHelpPolicy, DefaultPermissionPolicy, '
                            'LegacyAttachmentPolicy')
        perm_sys = PermissionSystem(self.env)
        perm_sys.grant_permission('user_with_view', 'WIKI_VIEW')
        perm_sys.grant_permission('user_with_modify', 'WIKI_MODIFY')
        perm_sys.grant_permission('user_with_delete', 'WIKI_DELETE')
        perm_sys.grant_permission('user_with_admin', 'WIKI_ADMIN')
        for name in ('WikiStart', 'RandomPage', 'TracGuide'):
            page = WikiPage(self.env, name)
            page.text = "The Text"
            page.save('the creator', 'the comment')

    def tearDown(self):
        self.env.reset_db()

    def test_wiki_view_permission(self):
        """User with WIKI_VIEW can view any page."""
        perm_cache = PermissionCache(self.env, 'user_with_view')
        self.assertTrue('WIKI_VIEW' in perm_cache('wiki', 'WikiStart'))
        self.assertTrue('WIKI_VIEW' in perm_cache('wiki', 'RandomPage'))
        self.assertTrue('WIKI_VIEW' in perm_cache('wiki', 'TracGuide'))

    def test_no_wiki_modify_permission(self):
        """User with WIKI_MODIFY can't modify help pages."""
        perm_cache = PermissionCache(self.env, 'user_with_modify')
        self.assertTrue('WIKI_MODIFY' in perm_cache('wiki', 'WikiStart'))
        self.assertTrue('WIKI_MODIFY' in perm_cache('wiki', 'RandomPage'))
        self.assertFalse('WIKI_MODIFY' in perm_cache('wiki', 'TracGuide'))

    def test_no_wiki_delete_permission(self):
        """User with WIKI_DELETE can't delete help pages."""
        perm_cache = PermissionCache(self.env, 'user_with_delete')
        self.assertTrue('WIKI_DELETE' in perm_cache('wiki', 'WikiStart'))
        self.assertTrue('WIKI_DELETE' in perm_cache('wiki', 'RandomPage'))
        self.assertFalse('WIKI_DELETE' in perm_cache('wiki', 'TracGuide'))

    def test_no_wiki_admin_permission(self):
        """User with WIKI_ADMIN can't modify or delete help pages."""
        perm_cache = PermissionCache(self.env, 'user_with_admin')
        self.assertTrue('WIKI_ADMIN' in perm_cache('wiki', 'WikiStart'))
        self.assertTrue('WIKI_ADMIN' in perm_cache('wiki', 'RandomPage'))
        self.assertFalse('WIKI_ADMIN' in perm_cache('wiki', 'TracGuide'))

    def test_help_page_has_notice(self):
        """Help page has notice inserted into top of page content."""
        req = MockRequest(self.env, authname='user_with_view',
                          path_info='/wiki/TracGuide')
        dispatcher = RequestDispatcher(self.env)
        self.assertRaises(RequestDone, dispatcher.dispatch, req)
        self.assertIn("The TracGuide is not editable on this site.",
                      req.response_sent.getvalue())

    def test_non_help_page_has_no_notice(self):
        """Non-help page doesn't have notice inserted into top of page
        content."""
        req = MockRequest(self.env, authname='user_with_view',
                          path_info='/wiki/WikiStart')
        dispatcher = RequestDispatcher(self.env)
        self.assertRaises(RequestDone, dispatcher.dispatch, req)
        self.assertNotIn("The TracGuide is not editable on this site.",
                         req.response_sent.getvalue())

    def test_only_view_page_has_notice(self):
        """Help page history doesn't have a notice inserted into top
        of page content. Regression test for #12613."""
        req = MockRequest(self.env, authname='user_with_view',
                          path_info='/wiki/TracGuide',
                          args={'action': 'history'})
        dispatcher = RequestDispatcher(self.env)
        self.assertRaises(RequestDone, dispatcher.dispatch, req)
        self.assertNotIn("The TracGuide is not editable on this site.",
                         req.response_sent.getvalue())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ReadonlyHelpPolicyTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
