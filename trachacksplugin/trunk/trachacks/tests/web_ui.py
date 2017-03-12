# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
import StringIO

from trac.attachment import Attachment
from trac.perm import PermissionCache, PermissionSystem
from trac.test import EnvironmentStub, MockRequest
from trac.ticket import model
from trac.web.api import RequestDone
from trac.web.main import RequestDispatcher
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

import trachacks.web_ui


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


class TracHacksPolicyTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=('trac.*', 'trachacks.*'))
        self.env.config.set('trac', 'permission_policies',
                            'TracHacksPolicy, DefaultPermissionPolicy, '
                            'LegacyAttachmentPolicy')
        self._create_component('Project1', 'maintainer')
        self._create_component('Project2', 'othermaintainer')
        PermissionSystem(self.env).grant_permission('authenticated',
                                                    'TICKET_CHGPROP')

    def tearDown(self):
        self.env.reset_db()

    def _create_ticket(self, reporter, component):
        ticket = model.Ticket(self.env)
        ticket['reporter'] = reporter
        ticket['summary'] = 'The summary'
        ticket['description'] = 'The text.'
        ticket['component'] = component
        ticket.insert()
        return ticket

    def _create_component(self, name, owner):
        component = model.Component(self.env)
        component.name = name
        component.owner = owner
        component.insert()

    def _create_page(self, name):
        page = WikiPage(self.env, name)
        page.text = 'The text'
        page.save('somebody', 'Page created')
        return page

    def _insert_attachment(self, author, parent_resource):
        attachment = Attachment(self.env, parent_resource.realm,
                                parent_resource.id)
        attachment.author = author
        attachment.insert('file.txt', StringIO.StringIO(''), 0)
        return attachment

    def test_reporter_can_edit_own_ticket_description(self):
        """Authenticated user can modify description of ticket they
        reported.
        """
        ticket = self._create_ticket('somebody', 'Project1')

        perm_cache = PermissionCache(self.env, 'somebody')
        self.assertIn('TICKET_EDIT_DESCRIPTION', perm_cache(ticket.resource))

    def test_reporter_no_edit_other_ticket_description(self):
        """Authenticated user cannot modify description of ticket they
        didn't report.
        """
        ticket = self._create_ticket('somebodyelse', 'Project1')

        perm_cache = PermissionCache(self.env, 'somebody')
        self.assertNotIn('TICKET_EDIT_DESCRIPTION',
                         perm_cache(ticket.resource))

    def test_anonymous_no_edit_ticket_description(self):
        """Anonymous user cannot modify description of ticket they
        reported.
        """
        ticket = self._create_ticket('anonymous', 'Project1')

        perm_cache = PermissionCache(self.env, 'anonymous')
        self.assertNotIn('TICKET_EDIT_DESCRIPTION',
                         perm_cache(ticket.resource))

    def test_maintainer_can_edit_ticket_description_for_own_project(self):
        """Maintainer can edit ticket cc, comment and description for
        their own project.
        """
        ticket = self._create_ticket('somebody', 'Project1')

        perm_cache = PermissionCache(self.env, 'maintainer')
        self.assertIn('TICKET_EDIT_CC', perm_cache(ticket.resource))
        self.assertIn('TICKET_EDIT_COMMENT', perm_cache(ticket.resource))
        self.assertIn('TICKET_EDIT_DESCRIPTION', perm_cache(ticket.resource))

    def test_maintainer_no_edit_ticket_description_for_other_project(self):
        """Maintainer cannot edit ticket cc, comment and description for
        other project.
        """
        ticket = self._create_ticket('somebody', 'Project2')

        perm_cache = PermissionCache(self.env, 'maintainer')
        self.assertNotIn('TICKET_EDIT_CC', perm_cache(ticket.resource))
        self.assertNotIn('TICKET_EDIT_COMMENT', perm_cache(ticket.resource))
        self.assertNotIn('TICKET_EDIT_DESCRIPTION',
                         perm_cache(ticket.resource))

    def test_user_can_delete_their_own_ticket_attachments(self):
        """Authenticated user can delete their own ticket attachments.
        """
        ticket = self._create_ticket('somebody', 'Project1')
        attachment = self._insert_attachment('somebody', ticket.resource)

        perm_cache = PermissionCache(self.env, 'somebody')
        self.assertIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_user_no_delete_other_ticket_attachments(self):
        """Authenticated user cannot delete other ticket attachments."""
        ticket = self._create_ticket('somebody', 'Project1')
        attachment = self._insert_attachment('somebodyelse', ticket.resource)

        perm_cache = PermissionCache(self.env, 'somebody')
        self.assertNotIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_anonymous_cannot_delete_ticket_attachments(self):
        """Anonymous cannot delete ticket attachments."""
        ticket = self._create_ticket('anonymous', 'Project1')
        attachment = self._insert_attachment('anonymous', ticket.resource)

        perm_cache = PermissionCache(self.env, 'anonymous')
        self.assertNotIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_maintainer_can_delete_ticket_attachments_for_own_project(self):
        """Maintainer can delete ticket attachments for their own project."""
        ticket = self._create_ticket('somebody', 'Project1')
        attachment = self._insert_attachment('somebody', ticket.resource)

        perm_cache = PermissionCache(self.env, 'maintainer')
        self.assertIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_maintainer_no_delete_ticket_attachments_for_other_project(self):
        """Maintainer cannot delete ticket attachments for other project.
        """
        ticket = self._create_ticket('somebody', 'Project2')
        attachment = self._insert_attachment('somebody', ticket.resource)

        perm_cache = PermissionCache(self.env, 'maintainer')
        self.assertNotIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_user_can_delete_their_own_wiki_attachments(self):
        """Authenticated user can delete their own wiki attachments."""
        page = self._create_page('Project1')
        attachment = self._insert_attachment('somebody', page.resource)

        perm_cache = PermissionCache(self.env, 'somebody')
        self.assertIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_user_no_delete_other_wiki_attachments(self):
        """Authenticated user cannot delete other wiki attachments."""
        page = self._create_page('Project1')
        attachment = self._insert_attachment('somebodyelse', page.resource)

        perm_cache = PermissionCache(self.env, 'somebody')
        self.assertNotIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_anonymous_cannot_delete_wiki_attachments(self):
        """Anonymous cannot delete wiki attachments."""
        page = self._create_page('Project1')
        attachment = self._insert_attachment('anonymous', page.resource)

        perm_cache = PermissionCache(self.env, 'anonymous')
        self.assertNotIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_maintainer_can_delete_wiki_attachments_for_own_project(self):
        """Maintainer can delete wiki attachments for their own project."""
        page = self._create_page('Project1')
        attachment = self._insert_attachment('somebody', page.resource)

        perm_cache = PermissionCache(self.env, 'maintainer')
        self.assertIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))

    def test_maintainer_no_delete_wiki_attachments_for_other_project(self):
        """Maintainer cannot delete wiki attachments for other project."""
        page = self._create_page('Project2')
        attachment = self._insert_attachment('somebody', page.resource)

        perm_cache = PermissionCache(self.env, 'maintainer')
        self.assertNotIn('ATTACHMENT_DELETE', perm_cache(attachment.resource))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ReadonlyHelpPolicyTestCase))
    suite.addTest(unittest.makeSuite(TracHacksPolicyTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
