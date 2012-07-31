# -*- coding: utf-8 -*-

import unittest

from trac.test import EnvironmentStub, Mock, MockPerm
from trac.util.compat import any
from trac.web.api import RequestDone
from trac.web.href import Href

from iniadmin.iniadmin import IniAdminPlugin


class IniAdminTestCase(unittest.TestCase):

    def setUp(self):
        def redirect(self):
            raise RequestDone

        self.env = EnvironmentStub(enable=[IniAdminPlugin])
        self.iniadmin = IniAdminPlugin(self.env)
        self.req = Mock(base_path='', chrome={}, method='GET', args={},
                        session={}, abs_href=Href('/'), href=Href('/'),
                        locale=None, perm=MockPerm(), authname=None, tz=None,
                        redirect=redirect)

    def tearDown(self):
        self.env.reset_db()

    def test_excludes(self):
        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'iniadmin', '')
        self.assertFalse(any(opt['name'] == 'excludes'
                             for opt in data['iniadmin']['options']))

        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'trac', '')
        self.assertTrue(any(opt['name'] == 'database'
                            for opt in data['iniadmin']['options']))

    def test_passwords(self):
        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'trac', '')
        self.assertTrue(any(opt['type'] == 'password'
                            for opt in data['iniadmin']['options']
                            if opt['name'] == 'database'))

        template, data = self.iniadmin.render_admin_panel(
            self.req, 'tracini', 'notification', '')
        self.assertTrue(any(opt['type'] == 'password'
                            for opt in data['iniadmin']['options']
                            if opt['name'] == 'smtp_password'))

    def test_post_excludes(self):
        config = self.env.config
        excludes = self.env.config.get('iniadmin', 'excludes')

        self.req.method = 'POST'
        self.req.args['name'] = 'Updated via iniadmin'
        self.assertRaises(RequestDone,
                          self.iniadmin.render_admin_panel,
                          self.req, 'tracini', 'project', '')
        self.assertEqual('Updated via iniadmin', config.get('project', 'name'))

        self.req.method = 'POST'
        self.req.args['excludes'] = '***'
        self.assertRaises(RequestDone,
                          self.iniadmin.render_admin_panel,
                          self.req, 'tracini', 'iniadmin', '')
        self.assertEqual(excludes, config.get('iniadmin', 'excludes'))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IniAdminTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
