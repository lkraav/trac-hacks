# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

from trac.perm import PermissionSystem
from trac.test import EnvironmentStub, MockRequest
from trac.web.api import RequestDone

from customfieldadmin.admin import CustomFieldAdminPage
from customfieldadmin.api import CustomFields


class CustomFieldAdminPageTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        ps = PermissionSystem(self.env)
        ps.grant_permission('admin', 'TICKET_ADMIN')
        self.plugin = CustomFieldAdminPage(self.env)
        self.api = CustomFields(self.env)

    def tearDown(self):
        self.env.destroy_db()

    def test_create(self):
        req = MockRequest(self.env, path_info='/admin/customfields',
                method='POST', authname='admin', args={
                    'add': True,
                     'name': "test",
                     'type': "textarea",
                     'label': "testing",
                     'format': "wiki",
                     'row': '9',
                }
        )
        with self.assertRaises(RequestDone):
            self.plugin.render_admin_panel(req, 'ticket', 'customfields', None)
        self.assertEquals([
            (u'test', u'textarea'),
            (u'test.cols', u'60'),
            (u'test.format', u'wiki'),
            (u'test.label', u'testing'),
            (u'test.options', u''),
            (u'test.order', u'1'),
            (u'test.rows', u'5'),
            (u'test.value', u''),
        ], sorted(list(self.env.config.options('ticket-custom'))))

    def test_add_optional_select(self):
        req = MockRequest(self.env, path_info='/admin/customfields',
                method='POST', authname='admin', args={
                    'add': True,
                    'name': "test",
                    'type': "select",
                    'label': "testing",
                    'options': "\r\none\r\ntwo"
                }
        )
        with self.assertRaises(RequestDone):
            self.plugin.render_admin_panel(req, 'ticket', 'customfields', None)
        self.assertEquals([
            (u'test', u'select'), (u'test.label', u'testing'),
            (u'test.options', u'|one|two'), (u'test.order', u'1'),
            (u'test.value', u'')
        ], sorted(list(self.env.config.options('ticket-custom'))))

    def test_apply_optional_select(self):
        # Reuse the added custom field that test verified to work
        self.test_add_optional_select()
        self.assertEquals('select',
                            self.env.config.get('ticket-custom', 'test'))
        # Now check that details are maintained across order change
        # that reads fields, deletes them, and creates them again
        # http://trac-hacks.org/ticket/1834#comment:5
        req = MockRequest(self.env, path_info='/admin/customfields',
                method='POST', authname='admin', args={
                    'apply': True,
                    'order_test': '2'
            }
        )
        with self.assertRaises(RequestDone):
            self.plugin.render_admin_panel(req, 'ticket', 'customfields', None)
        self.assertEquals([
            (u'test', u'select'), (u'test.label', u'testing'),
            (u'test.options', u'|one|two'), (u'test.order', u'2'),
            (u'test.value', u'')
        ], sorted(list(self.env.config.options('ticket-custom'))))

    def test_edit_optional_select(self):
        self.test_add_optional_select()
        self.assertEquals('select',
                self.env.config.get('ticket-custom', 'test'))
        req = MockRequest(self.env, path_info='/admin/customfields',
                method='POST', authname='admin', args={
                    'save': True, 'name': u'test', 'label': u'testing',
                    'type': u'select', 'value': u'',
                    'options': u'\r\none\r\ntwo'
                }
        )
        with self.assertRaises(RequestDone):
            self.plugin.render_admin_panel(req, 'ticket', 'customfields',
                                           'test')
        self.assertEquals([
            (u'test', u'select'), (u'test.label', u'testing'),
            (u'test.options', u'|one|two'), (u'test.order', u'2'),
            (u'test.value', u'')
        ], sorted(list(self.env.config.options('ticket-custom'))))

    def test_order_with_mismatched_keys(self):
        # http://trac-hacks.org/ticket/11540
        self.api.create_custom_field({
            'name': u'one', 'format': 'plain', 'value': '',
            'label': u'One', 'type': u'text', 'order': 1
        })
        req = MockRequest(self.env, path_info='/admin/customfields',
                method='POST', authname='admin', args={
                    'apply': True,
                    'order_two': '1'
                }
        )
        with self.assertRaises(RequestDone):
            self.plugin.render_admin_panel(req, 'ticket', 'customfields', None)
