# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Noah Kantrowitz
# Copyright (C) 2012-2017 Ryan J Ollos
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from trac.perm import PermissionCache, PermissionSystem
from trac.test import EnvironmentStub
from trac.ticket import Ticket

from privatetickets.policy import PrivateTicketsPolicy


def create_ticket(env, reporter=None, owner=None, cc=None):
    ticket = Ticket(env)
    ticket['reporter'] = reporter
    ticket['owner'] = owner
    ticket['cc'] = cc or ''
    ticket.insert()
    return ticket


class UserTestCase(unittest.TestCase):
    """Test case for user actions."""

    def setUp(self):
        self.env = EnvironmentStub(enable=('trac.*', 'privatetickets.*'))
        self.env.config.set('trac', 'permission_policies',
                            'PrivateTicketsPolicy,DefaultPermissionPolicy')
        self.ps = PermissionSystem(self.env)

    def tearDown(self):
        self.env = None

    def create_ticket(self, reporter=None, owner=None, cc=None):
        return create_ticket(self.env, reporter, owner, cc)

    def _test_action_on_ticket(self, result, actions, **props):
        viewer = 'user1'
        for action in actions:
            self.ps.grant_permission(viewer, action)

        ticket = self.create_ticket(**props)
        perm = PermissionCache(self.env, viewer, ticket.resource)

        if result:
            self.assertTrue('TICKET_VIEW' in perm)
        else:
            self.assertFalse('TICKET_VIEW' in perm)

    def test_reporter_has_ticket_view_for_resource(self):
        """User with TICKET_VIEW for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW',), reporter='user1')

    def test_reporter_has_ticket_view_reporter_for_resource(self):
        """User with TICKET_VIEW_REPORTER for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_REPORTER'),
                                    reporter='user1')

    def test_reporter_has_ticket_self_for_resource(self):
        """User with TICKET_VIEW_SELF for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_SELF'),
                                    reporter='user1')

    def test_reporter_no_ticket_view_for_resource(self):
        """User with only TICKET_VIEW can view any ticket."""
        self._test_action_on_ticket(True, ('TICKET_VIEW',), reporter='user2')

    def test_reporter_no_ticket_view_reporter_for_resource(self):
        """User without TICKET_VIEW_REPORTER for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_REPORTER'),
                                    reporter='user2')

    def test_reporter_no_ticket_view_self_for_resource(self):
        """User without TICKET_VIEW_SELF for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_SELF'),
                                    reporter='user2')

    def test_owner_has_ticket_view_for_resource(self):
        """User with TICKET_VIEW for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW',), owner='user1')

    def test_owner_has_ticket_view_owner_for_resource(self):
        """User with TICKET_VIEW_OWNER for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_OWNER'),
                                    owner='user1')

    def test_owner_has_ticket_view_self_for_resource(self):
        """User with TICKET_VIEW_SELF for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_SELF'),
                                    owner='user1')

    def test_owner_no_ticket_view_for_resource(self):
        """User with only TICKET_VIEW can view any ticket."""
        self._test_action_on_ticket(True, ('TICKET_VIEW',), owner='user2')

    def test_owner_no_ticket_view_owner_for_resource(self):
        """User without TICKET_VIEW_OWNER for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_OWNER'),
                                    owner='user2')

    def test_owner_no_ticket_view_self_for_resource(self):
        """User without TICKET_VIEW_SELF for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_SELF'),
                                    owner='user2')

    def test_cc_has_ticket_view_for_resource(self):
        """User with TICKET_VIEW for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW',), cc='user1')

    def test_cc_has_ticket_view_cc_for_resource(self):
        """User with TICKET_VIEW_CC for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_CC'),
                                    cc='user1')

    def test_cc_has_ticket_view_self_for_resource(self):
        """User with TICKET_VIEW_SELF for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_SELF'),
                                    cc='user1')

    def test_cc_no_ticket_view_for_resource(self):
        """User with only TICKET_VIEW can view any ticket."""
        self._test_action_on_ticket(True, ('TICKET_VIEW',), cc='user2')

    def test_cc_no_ticket_view_cc_for_resource(self):
        """User without TICKET_VIEW_CC for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_CC'),
                                    cc='user2')

    def test_cc_no_ticket_view_self_for_resource(self):
        """User without TICKET_VIEW_SELF for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_SELF'),
                                    cc='user2')


class GroupTestCase(unittest.TestCase):
    """Test case for group actions."""

    def setUp(self):
        self.env = EnvironmentStub(enable=('trac.*', 'privatetickets.*'))
        self.env.config.set('trac', 'permission_policies',
                            'PrivateTicketsPolicy,DefaultPermissionPolicy')
        self.ps = PermissionSystem(self.env)

    def tearDown(self):
        self.env = None

    def create_ticket(self, reporter=None, owner=None, cc=None):
        return create_ticket(self.env, reporter, owner, cc)

    def _test_action_on_ticket(self, result, actions, **props):
        viewer = 'user1'
        reporter = 'user2'
        owner = 'user3'
        cc = 'user4'
        for action in actions + ('group2', 'group3', 'group4', 'group5'):
            self.ps.grant_permission(viewer, action)
        self.ps.grant_permission(reporter, 'group2')
        self.ps.grant_permission(owner, 'group3')
        self.ps.grant_permission(cc, 'group4')
        # viewer does not share group5 with user5.

        ticket = self.create_ticket(**props)
        perm = PermissionCache(self.env, viewer, ticket.resource)

        if result:
            self.assertTrue('TICKET_VIEW' in perm)
        else:
            self.assertFalse('TICKET_VIEW' in perm)

    def test_reporter_has_ticket_view_for_resource(self):
        """User with TICKET_VIEW for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW',),
                                    reporter='user2')

    def test_reporter_has_ticket_view_reporter_group_for_resource(self):
        """User with TICKET_VIEW_REPORTER_GROUP for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW',
                                     'TICKET_VIEW_REPORTER_GROUP'),
                                    reporter='user2')

    def test_reporter_has_ticket_view_group_for_resource(self):
        """User with TICKET_VIEW_GROUP for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_GROUP'),
                                    reporter='user2')

    def test_reporter_no_ticket_view_for_resource(self):
        """User with only TICKET_VIEW can view any ticket."""
        self._test_action_on_ticket(True, ('TICKET_VIEW',), reporter='user5')

    def test_reporter_no_ticket_view_reporter_group_for_resource(self):
        """User without TICKET_VIEW_REPORTER_GROUP for resource cannot view.
        """
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW',
                                     'TICKET_VIEW_REPORTER_GROUP'),
                                    reporter='user5')

    def test_reporter_no_ticket_view_group_for_resource(self):
        """User without TICKET_VIEW_GROUP for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_GROUP'),
                                    reporter='user5')

    def test_owner_has_ticket_view_for_resource(self):
        """User with TICKET_VIEW for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW',), owner='user3')

    def test_owner_has_ticket_view_owner_group_for_resource(self):
        """User with TICKET_VIEW_OWNER_GROUP for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW',
                                     'TICKET_VIEW_OWNER_GROUP'),
                                    owner='user3')

    def test_owner_has_ticket_view_group_for_resource(self):
        """User with TICKET_VIEW_GROUP for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_GROUP'),
                                    owner='user3')

    def test_owner_no_ticket_view_for_resource(self):
        """User with only TICKET_VIEW can view any ticket."""
        self._test_action_on_ticket(True, ('TICKET_VIEW',), owner='user5')

    def test_owner_no_ticket_view_owner_group_for_resource(self):
        """User without TICKET_VIEW_OWNER_GROUP for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW',
                                     'TICKET_VIEW_OWNER_GROUP'),
                                    owner='user5')

    def test_owner_no_ticket_view_group_for_resource(self):
        """User without TICKET_VIEW_GROUP for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_GROUP'),
                                    owner='user5')

    def test_cc_has_ticket_view_for_resource(self):
        """User with only TICKET_VIEW can view any ticket."""
        self._test_action_on_ticket(True, ('TICKET_VIEW',), cc='user4')

    def test_cc_has_ticket_view_cc_group_for_resource(self):
        """User with TICKET_VIEW_CC_GROUP for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_CC_GROUP'),
                                    cc='user4')

    def test_cc_has_ticket_view_group_for_resource(self):
        """User with TICKET_VIEW_GROUP for resource can view."""
        self._test_action_on_ticket(True,
                                    ('TICKET_VIEW', 'TICKET_VIEW_GROUP'),
                                    cc='user4')

    def test_cc_no_ticket_view_for_resource(self):
        """User with only TICKET_VIEW can view any ticket."""
        self._test_action_on_ticket(True, ('TICKET_VIEW',), cc='user5')

    def test_cc_no_ticket_view_cc_group_for_resource(self):
        """User without TICKET_VIEW_CC_GROUP for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_CC_GROUP'),
                                    cc='user5')

    def test_cc_no_ticket_view_group_for_resource(self):
        """User without TICKET_VIEW_GROUP for resource cannot view."""
        self._test_action_on_ticket(False,
                                    ('TICKET_VIEW', 'TICKET_VIEW_GROUP'),
                                    cc='user5')


class SpecialTestCase(unittest.TestCase):
    """Test case for meta groups and meta permissions."""

    def setUp(self):
        self.env = EnvironmentStub(enable=('trac.*', 'privatetickets.*'))
        self.env.config.set('trac', 'permission_policies',
                            'PrivateTicketsPolicy,DefaultPermissionPolicy')
        self.ps = PermissionSystem(self.env)

    def tearDown(self):
        self.env = None

    def create_ticket(self, reporter=None, owner=None, cc=None):
        return create_ticket(self.env, reporter, owner, cc)

    def test_anonymous_can_view_all_tickets(self):
        """anonymous can view any ticket, private ticket permissions do not
        restrict access.
        """
        viewer = 'anonymous'
        for action in ('TICKET_VIEW', 'TICKET_VIEW_OWNER',
                       'TICKET_VIEW_REPORTER', 'TICKET_VIEW_CC'):
            self.ps.grant_permission(viewer, action)

        ticket1 = self.create_ticket(owner='user1')
        ticket2 = self.create_ticket(reporter='user2')
        ticket3 = self.create_ticket(cc='user3')
        perm1 = PermissionCache(self.env, viewer, ticket1.resource)
        perm2 = PermissionCache(self.env, viewer, ticket2.resource)
        perm3 = PermissionCache(self.env, viewer, ticket3.resource)

        self.assertTrue('TICKET_VIEW' in perm1)
        self.assertTrue('TICKET_VIEW' in perm2)
        self.assertTrue('TICKET_VIEW' in perm3)

    def test_trac_admin_can_view_all_tickets(self):
        """user with TRAC_ADMIN can view any ticket, private ticket
        permissions do not restrict access.
        """
        viewer = 'user1'
        for action in ('TRAC_ADMIN', 'TICKET_VIEW', 'TICKET_VIEW_OWNER',
                       'TICKET_VIEW_REPORTER', 'TICKET_VIEW_CC'):
            self.ps.grant_permission(viewer, action)

        ticket1 = self.create_ticket(owner='user2')
        ticket2 = self.create_ticket(reporter='user3')
        ticket3 = self.create_ticket(cc='user4')
        perm1 = PermissionCache(self.env, viewer, ticket1.resource)
        perm2 = PermissionCache(self.env, viewer, ticket2.resource)
        perm3 = PermissionCache(self.env, viewer, ticket3.resource)

        self.assertTrue('TICKET_VIEW' in perm1)
        self.assertTrue('TICKET_VIEW' in perm2)
        self.assertTrue('TICKET_VIEW' in perm3)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UserTestCase))
    suite.addTest(unittest.makeSuite(GroupTestCase))
    suite.addTest(unittest.makeSuite(SpecialTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
