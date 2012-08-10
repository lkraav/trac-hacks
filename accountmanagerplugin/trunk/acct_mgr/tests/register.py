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

from genshi.core  import Markup

from trac.perm  import PermissionCache, PermissionSystem
from trac.test  import EnvironmentStub, Mock

from acct_mgr.admin  import AccountManagerAdminPanels
from acct_mgr.api  import AccountManager, IAccountRegistrationInspector
from acct_mgr.db  import SessionStore
from acct_mgr.register  import GenericRegistrationInspector, \
                               RegistrationError, RegistrationModule, \
                               UsernameBasicCheck, UsernamePermCheck


class _BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'acct_mgr.*'])
        self.env.path = tempfile.mkdtemp()
        self.perm = PermissionSystem(self.env)

        # Register AccountManager actions.
        self.ap = AccountManagerAdminPanels(self.env)
        # Create a user reference in the permission system.
        self.perm.grant_permission('admin', 'ACCTMGR_USER_ADMIN')
        # Prepare a generic registration request.
        args = dict(username='', name='', email='')
        self.req = Mock(authname='anonymous', args=args)
        self.req.perm = PermissionCache(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)


class DummyRegInspectorTestCase(_BaseTestCase):
    """Check GenericRegistrationInspector properties via child classes."""
    def setUp(self):
        _BaseTestCase.setUp(self)

        class DummyRegistrationInspector(GenericRegistrationInspector):
            def validate_registration(self, req):
                if req.args.get('username') == 'dummy':
                    raise RegistrationError('Dummy check error')
                return

        self.check = DummyRegistrationInspector(self.env)

    def test_bad_check(self):
        class BadRegistrationInspector(GenericRegistrationInspector):
            """Child class, that is left as a copy of its base.

            Bad check class example, because check method is not implemented.
            """

        check = BadRegistrationInspector(self.env)
        # Default (empty) response for providing additional fields is safe.
        field_res = check.render_registration_fields(self.req)
        self.assertEqual(len(field_res), 2)
        self.assertEqual((Markup(field_res[0]), field_res[1]),
                         (Markup(''), {}))
        # Check class without 'validate_registration' implementation fails.
        self.assertRaises(NotImplementedError, check.validate_registration,
                          self.req)

    def test_dummy_check(self):
        # Check class with 'validate_registration' passes this test.
        self.assertEqual(self.check.validate_registration(self.req), None)

    def test_check_error(self):
        self.req.args['username'] = 'dummy'
        try:
            self.check.validate_registration(self.req)
            # Shouldn't reach that point.
            self.assertTrue(False)
        except RegistrationError, e:
            # Check error properties in detail.
            self.assertEqual(e.message, 'Dummy check error')
            self.assertEqual(e.title, 'Registration Error')


class UsernameBasicCheckTestCase(_BaseTestCase):
    def setUp(self):
        _BaseTestCase.setUp(self)
        self.env.config.set('account-manager', 'password_store',
                            'SessionStore')
        store = SessionStore(self.env)
        store.set_password('registered_user', 'password')

    def test_check(self):
        check = UsernameBasicCheck(self.env)
        req = self.req
        # Inspector doesn't provide additional fields.
        field_res = check.render_registration_fields(req)
        self.assertEqual(len(field_res), 2)
        self.assertEqual((Markup(field_res[0]), field_res[1]),
                         (Markup(''), {}))
        # 1st attempt: No input.
        self.assertRaises(RegistrationError, check.validate_registration,
                          req)
        # 2nd attempt: Illegal character.
        req.args['username'] = 'user:name'
        self.assertRaises(RegistrationError, check.validate_registration,
                          req)
        # 3rd attempt: Reserved word.
        req.args['username'] = 'Anonymous'
        self.assertRaises(RegistrationError, check.validate_registration,
                          req)
        # 4th attempt: Existing user.
        req.args['username'] = 'registered_user'
        self.assertRaises(RegistrationError, check.validate_registration,
                          req)
        # 5th attempt: Finally some valid input.
        req.args['username'] = 'user'
        self.assertEqual(check.validate_registration(req), None)


class UsernamePermCheckTestCase(_BaseTestCase):
    def test_check(self):
        check = UsernamePermCheck(self.env)
        req = self.req
        # Inspector doesn't provide additional fields.
        field_res = check.render_registration_fields(req)
        self.assertEqual(len(field_res), 2)
        self.assertEqual((Markup(field_res[0]), field_res[1]),
                         (Markup(''), {}))
        # 1st attempt: No username, hence no conflic possible.
        self.assertEqual(check.validate_registration(req), None)
        # 2nd attempt: No permission assigned for that username.
        req.args['username'] = 'user'
        self.assertEqual(check.validate_registration(req), None)
        # 3rd attempt: Explicite permission assigned for that username.
        req.args['username'] = 'admin'
        self.assertRaises(RegistrationError, check.validate_registration,
                          req)
        # 4th attempt: As before, but request done by admin user.
        req.perm = PermissionCache(self.env, 'admin')
        self.assertEqual(check.validate_registration(req), None)


class RegistrationModuleTestCase(_BaseTestCase):
    def setUp(self):
        _BaseTestCase.setUp(self)
        self.rmod = RegistrationModule(self.env)
        self.reg_template = 'register.html'
        self.req.method = 'POST'

    def test_check(self):
        # Default configuration: All provided checks enabled.
        response = self.rmod.process_request(self.req)
        self.assertEqual(response[0], self.reg_template)
        # Custom configuration: Do basic username checks only.
        self.req.args['username'] = 'admin'
        self.req.args['email'] = 'admin@foo.bar'
        self.env.config.set('account-manager', 'register_check',
                            'UsernameBasicCheck')
        response = self.rmod.process_request(self.req)
        self.assertEqual(response[0], self.reg_template)
        # Custom configuration: No check at all, if you insist.
        self.env.config.set('account-manager', 'register_check',
                            '')
        response = self.rmod.process_request(self.req)
        self.assertEqual(response[0], self.reg_template)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DummyRegInspectorTestCase, 'test'))
    suite.addTest(unittest.makeSuite(UsernameBasicCheckTestCase, 'test'))
    suite.addTest(unittest.makeSuite(UsernamePermCheckTestCase, 'test'))
    suite.addTest(unittest.makeSuite(RegistrationModuleTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
