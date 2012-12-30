# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann <hoff.st@web.de>

import shutil
import tempfile
import unittest

from trac.core import TracError
from trac.perm import PermissionSystem
from trac.test import EnvironmentStub, Mock

from acct_mgr.api import AccountManager
from acct_mgr.db  import SessionStore


class _BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'acct_mgr.api.*',
                        'acct_mgr.db.SessionStore']
        )
        self.env.path = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.env.path)


class AccountManagerTestCase(_BaseTestCase):

    def setUp(self):
        _BaseTestCase.setUp(self)
        self.mgr = AccountManager(self.env)

        self.store = SessionStore(self.env)
        self.store.set_password('user', 'passwd')

    def test_set_password(self):
        # Can't work without at least one password store.
        self.assertRaises(TracError, self.mgr.set_password, 'user', 'passwd')
        self.env.config.set(
            'account-manager', 'password_store', 'SessionStore')
        self.mgr.set_password('user', 'passwd')
        # Refuse to overwrite existing credetialy, if requested.
        self.assertRaises(TracError, self.mgr.set_password, 'user', 'passwd',
                          overwrite=False)


class PermissionTestCase(_BaseTestCase):

    def setUp(self):
        _BaseTestCase.setUp(self)
        self.perm = PermissionSystem(self.env)
        self.req = Mock()
        self.actions = ['ACCTMGR_ADMIN', 'ACCTMGR_CONFIG_ADMIN',
                        'ACCTMGR_USER_ADMIN', 'EMAIL_VIEW', 'USER_VIEW']

   # Tests

    def test_available_actions(self):
        for action in self.actions:
            self.failIf(action not in self.perm.get_actions())

    def test_available_actions_no_perms(self):
        for action in self.actions:
            self.assertFalse(self.perm.check_permission(action, 'anonymous'))

    def test_available_actions_config_admin(self):
        user = 'config_admin'
        self.perm.grant_permission(user, 'ACCTMGR_CONFIG_ADMIN')
        actions = [self.actions[0]] + self.actions[2:]
        for action in actions:
            self.assertFalse(self.perm.check_permission(action, user))

    def test_available_actions_user_admin(self):
        user = 'user_admin'
        self.perm.grant_permission(user, 'ACCTMGR_USER_ADMIN')
        for action in self.actions[2:]:
            self.assertTrue(self.perm.check_permission(action, user))
        for action in self.actions[:2] + ['TRAC_ADMIN']:
            self.assertFalse(self.perm.check_permission(action, user))

    def test_available_actions_full_perms(self):
        perm_map = dict(acctmgr_admin='ACCTMGR_ADMIN', trac_admin='TRAC_ADMIN')
        for user in perm_map:
            self.perm.grant_permission(user, perm_map[user])
            for action in self.actions:
                self.assertTrue(self.perm.check_permission(action, user))
            if user != 'trac_admin':
                self.assertFalse(self.perm.check_permission('TRAC_ADMIN',
                                                            user))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AccountManagerTestCase, 'test'))
    suite.addTest(unittest.makeSuite(PermissionTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
