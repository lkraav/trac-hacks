# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
#
# License: 3-clause BSD
#
import unittest

from ticketfieldfilter.web_ui import TicketFieldFilter
from trac.test import EnvironmentStub, MockRequest
from trac.web.api import RequestDone


class TestConfiguration(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        self.plugin = TicketFieldFilter(self.env)

    def test_ticket_fields_defect_all(self):
        self.env.config.set("ticket-field-filter", 'defect.fields', '+')
        res = self.plugin.get_configuration_for_tkt_types()
        self.assertEqual(3, len(res))
        tkt_fields, fields_readonly, field_perms = res
        # This will break when Trac doesn't default to [defect, task, enhancement] anymore
        self.assertEqual(3, len(tkt_fields))
        self.assertEqual(3, len(fields_readonly))
        self.assertEqual(3, len(field_perms))

        self.assertNotIn('+', tkt_fields['defect'])

    def test_parse_permission_single_field(self):
        permissions = self.env.config.get("ticket-field-filter", 'defect.permission', None)
        self.assertIsNone(permissions)
        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertEqual(1, len(res))
        self.assertIn('cc', res)
        self.assertSequenceEqual(['BAR'], res['cc'])

        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR|FOO|BAZ')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)  # res: {'cc': ['BAR', 'FOO', 'BAZ']}
        self.assertEqual(1, len(res))
        self.assertIn('cc', res)
        for perm in ('BAR', 'FOO', 'BAZ'):
            self.assertIn(perm, res['cc'])

    def test_parse_permission_multiple_fields(self):
        permissions = self.env.config.get("ticket-field-filter", 'defect.permission', None)
        self.assertIsNone(permissions)
        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR,keywords:BAR')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)  # res: {'cc': ['BAR'], 'keywords': ['BAR']}
        self.assertEqual(2, len(res))
        for item in ('cc', 'keywords'):
            self.assertIn(item, res)
            self.assertSequenceEqual(['BAR'], res[item])

        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR|FOO,keywords:BAR|BAZ')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertEqual(2, len(res))
        for item in ('cc', 'keywords'):
            self.assertIn(item, res)
        self.assertSequenceEqual(['BAR', 'FOO'], res['cc'])
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])

    def test_get_configuration_multiple_fields_perm(self):
        permissions = self.env.config.get("ticket-field-filter", 'defect.permission', None)
        self.assertIsNone(permissions)
        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR|FOO,keywords:BAR|BAZ')
        field_info, ro_info, field_perms = self.plugin.get_configuration_for_tkt_types()
        self.assertEqual(0, len(field_perms['task']))
        self.assertEqual(0, len(field_perms['enhancement']))
        res = field_perms['defect']
        self.assertEqual(2, len(res))
        for item in ('cc', 'keywords'):
            self.assertIn(item, res)
        self.assertSequenceEqual(['BAR', 'FOO'], res['cc'])
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])

    def test_render_admin_page_clear_single_field_perm(self):
        """Clear permissions of a single field which is the only one"""
        # Setup data
        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertEqual(1, len(res))
        self.assertSequenceEqual(['BAR'], res['cc'])

        # Delete permissions for field 'cc'
        # Note that there is no 'sel' arg here
        req = MockRequest(self.env, method='POST', args={'save': 'Save it!', 'type': 'defect', 'field': 'cc'})
        try:
            self.plugin.render_admin_panel(req, '', 'ticketfieldfilter', 'defect')
        except RequestDone:
            pass
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertEqual(0, len(res))

    def test_render_admin_page_clear_one_field_perm(self):
        """Clear permissions of one field while leavin another alone"""
        # Setup data
        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR|FOO,keywords:BAR|BAZ')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertSequenceEqual(['BAR', 'FOO'], res['cc'])
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])

        # Delete permissions for field 'cc'
        # Note that there is no 'sel' arg here
        req = MockRequest(self.env, method='POST', args={'save': 'Save it!', 'type': 'defect', 'field': 'cc'})
        try:
            self.plugin.render_admin_panel(req, '', 'ticketfieldfilter', 'defect')
        except RequestDone:
            pass

        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        print(self.plugin.field_perms)
        self.assertEqual(1, len(res))
        self.assertNotIn('cc', res)
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])

    def test_render_admin_page_single_field_add_perm(self):
        """Two fields with permissions. We add a new permission to one field."""
        # Setup data
        self.env.config.set("ticket-field-filter", 'defect.permission', 'cc:BAR|FOO,keywords:BAR|BAZ')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertSequenceEqual(['BAR', 'FOO'], res['cc'])
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])

        # Note that there is no 'sel' arg here
        sel = ['BAR', 'FOO', 'BAZ']
        req = MockRequest(self.env, method='POST',
                          args={'save': 'Save it!', 'type': 'defect', 'field': 'cc', 'sel': sel})
        self.assertRaises(RequestDone, self.plugin.render_admin_panel, req, '', 'ticketfieldfilter', 'defect')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertEqual(2, len(res))
        for item in ('cc', 'keywords'):
            self.assertIn(item, res)
        self.assertSequenceEqual(['BAR', 'FOO', 'BAZ'], res['cc'])
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])

    def test_render_admin_page_add_field_perm(self):
        """Obe field with permissions. We add another field."""
        # Setup data
        self.env.config.set("ticket-field-filter", 'defect.permission', 'keywords:BAR|BAZ')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertEqual(1, len(res))
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])

        # Note that there is no 'sel' arg here
        sel = 'BAR'
        req = MockRequest(self.env, method='POST',
                          args={'save': 'Save it!', 'type': 'defect', 'field': 'cc', 'sel': sel})
        self.assertRaises(RequestDone, self.plugin.render_admin_panel, req, '', 'ticketfieldfilter', 'defect')
        data = self.env.config.getlist('ticket-field-filter', 'defect.permission', [])
        res = self.plugin.parse_permission_entry(data)
        self.assertEqual(2, len(res))
        for item in ('cc', 'keywords'):
            self.assertIn(item, res)
        self.assertSequenceEqual(['BAR'], res['cc'])
        self.assertSequenceEqual(['BAR', 'BAZ'], res['keywords'])


if __name__ == '__main__':
    unittest.main()
