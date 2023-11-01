# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2023 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import parse_version
import unittest
import sys
import lxml.html

from trac import __version__
from trac.test import EnvironmentStub, MockRequest
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.ticket.query import QueryModule
from trac.ticket.web_ui import TicketModule
from trac.web.chrome import Chrome
from trac.web.main import RequestDispatcher

from ..api import TicketFieldsLayoutSetup
from ..web_ui import TicketFieldsLayoutModule


if sys.version_info[0] != 2:
    unicode = str


_parsed_version = parse_version(__version__)


class TicketFieldsLayoutTestCase(unittest.TestCase):

    maxDiff = None

    has_owner_field = _parsed_version < parse_version('1.2')
    if has_owner_field:
        hidden_fields = ('summary', 'reporter', 'description', 'owner')
    else:
        hidden_fields = ('summary', 'reporter', 'description')

    def setUp(self):
        env = EnvironmentStub(default_data=True,
                              enable=['trac.*', TicketFieldsLayoutSetup,
                                      TicketFieldsLayoutModule])
        env.needs_upgrade()
        self.env = env
        self.config = env.config
        self.dispatcher = RequestDispatcher(env)
        self.tktmod = TicketModule(env)
        self.querymod = QueryModule(env)

    def tearDown(self):
        self.env.reset_db()

    def _create_ticket(self, **kwargs):
        ticket = Ticket(self.env)
        for name in kwargs:
            ticket[name] = kwargs[name]
        ticket.insert()
        return ticket

    def _reset_ticket_fields(self):
        TicketSystem(self.env).reset_ticket_fields()

    def _parse_html(self, content):
        return lxml.html.fromstring(content)

    def _make_req(self, path_info=None):
        return MockRequest(self.env, path_info=path_info)

    def _process_request(self, req, mod):
        self.assertTrue(mod.match_request(req))
        return mod.process_request(req)

    def _post_process_request(self, req, *resp):
        return self.dispatcher._post_process_request(req, *resp)

    def _render(self, req, mod):
        resp = self._process_request(req, mod)
        resp = self._post_process_request(req, *resp)
        chrome = Chrome(self.env)
        content = chrome.render_template(req, *resp)
        if isinstance(content, unicode):
            return content
        if isinstance(content, bytes):
            return content.decode('utf-8')
        return u''.join(chunk.decode('utf-8')
                        if isinstance(chunk, bytes) else
                        chunk for chunk in content)

    def _render_ticket_page(self, req):
        return self._render(req, self.tktmod)

    def _test_script_data_in_query_page(self, ticketfieldslayout):
        req = self._make_req('/query')
        resp = self._process_request(req, self.querymod)
        resp = self._post_process_request(req, *resp)
        script_data = req.chrome.get('script_data', {})
        self.assertIn('ticketfieldslayout', set(script_data))
        self.assertEqual(ticketfieldslayout['fields'],
                         script_data['ticketfieldslayout']['fields'])
        self.assertEqual(ticketfieldslayout['groups'],
                         script_data['ticketfieldslayout']['groups'])
        self.assertEqual(ticketfieldslayout, script_data['ticketfieldslayout'])

    if not hasattr(unittest.TestCase, 'assertIn'):
        def assertIn(self, first, second, msg=None):
            if first not in second:
                self.fail(msg or '%r not in %r' % (first, second))

    if not hasattr(unittest.TestCase, 'assertNotIn'):
        def assertNotIn(self, first, second, msg=None):
            if first in second:
                self.fail(msg or '%r in %r' % (first, second))

    def test_hidden_fields(self):
        self.config.set('ticketfieldslayout', 'fields',
                        'summary,reporter,owner,description')

        req = self._make_req('/newticket')
        content = self._render_ticket_page(req)
        parsed = self._parse_html(content)
        elements = parsed.xpath('.//fieldset[@id="properties"]')
        self.assertEqual(1, len(elements))
        fieldset = elements[0]

        positions = {}
        for field in self.hidden_fields:
            self.assertTrue(fieldset.xpath('.//label[@for="field-%s"]' %
                                           field))
            self.assertTrue(fieldset.xpath('.//*[@name="field_%s"]' % field))
            positions[field] = content.index(' name="field_%s"' % field)
        self.assertEqual(self.hidden_fields,
                         tuple(sorted(positions, key=positions.get)))

        for field in ('type', 'priority', 'milestone', 'component', 'version',
                      'keywords'):
            self.assertFalse(fieldset.xpath('.//label[@for="field-%s"]' %
                                            field), content)
            self.assertFalse(fieldset.xpath('.//*[@name="field_%s"]' % field))

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        content = self._render_ticket_page(req)
        elements = parsed.xpath('.//table[@class="properties"]')
        self.assertEqual(1, len(elements))
        table = elements[0]

        positions = {}
        for field in ('reporter', 'owner'):
            self.assertTrue(table.xpath('.//th[@id="h_%s"]' % field))
            self.assertTrue(table.xpath('.//*[@headers="h_%s"]' % field))
            positions[field] = content.index(' headers="h_%s"' % field)
        self.assertEqual(['reporter', 'owner'],
                         sorted(positions, key=positions.get))
        for field in ('summary', 'description', 'type'):
            self.assertFalse(table.xpath('.//th[@id="h_%s"]' % field))
            self.assertFalse(table.xpath('.//*[@headers="h_%s"]' % field))

        self._test_script_data_in_query_page(
            {'fields': ['resolution', 'status', 'time', 'changetime',
                        'summary', 'reporter', 'owner', 'description', 'id'],
             'groups': {}})

    def test_custom_fields(self):
        fields = ['f_radio', 'f_select', 'f_checkbox', 'f_textarea', 'f_text',
                  'summary', 'reporter', 'owner', 'description']
        for name, value in (('f_text', 'text'),
                            ('f_text.order', '1'),
                            ('f_textarea', 'textarea'),
                            ('f_textarea.order', '2'),
                            ('f_checkbox', 'checkbox'),
                            ('f_checkbox.order', '3'),
                            ('f_select', 'select'),
                            ('f_select.order', '4'),
                            ('f_select.options', '1st|2nd|3rd'),
                            ('f_radio', 'radio'),
                            ('f_radio.order', '5'),
                            ('f_radio.options', 'lv1|lv2|lv3')):
            self.config.set('ticket-custom', name, value)
        self.config.set('ticketfieldslayout', 'fields', ','.join(fields))

        req = self._make_req('/newticket')
        content = self._render_ticket_page(req)
        parsed = self._parse_html(content)
        elements = parsed.xpath('.//fieldset[@id="properties"]')
        self.assertEqual(1, len(elements))
        fieldset = elements[0]

        positions = {}
        for field in fields:
            if field == 'owner' and not self.has_owner_field:
                continue
            if field != 'f_radio':
                self.assertTrue(fieldset.xpath('.//label[@for="field-%s"]' %
                                               field))
            self.assertTrue(fieldset.xpath('.//*[@name="field_%s"]' % field))
            positions[field] = content.index(' name="field_%s"' % field)
        expected = ['f_radio', 'f_select', 'f_checkbox', 'f_textarea',
                    'f_text', 'summary', 'reporter', 'description']
        if self.has_owner_field:
            expected.append('owner')
        self.assertEqual(expected, sorted(positions, key=positions.get))

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        content = self._render_ticket_page(req)
        parsed = self._parse_html(content)
        elements = parsed.xpath('.//table[@class="properties"]')
        self.assertEqual(1, len(elements))
        table = elements[0]

        positions = {}
        for field in set(fields) - set(('summary', 'description')):
            self.assertTrue(table.xpath('.//th[@id="h_%s"]' % field))
            self.assertTrue(table.xpath('.//*[@headers="h_%s"]' % field))
            positions[field] = content.index(' headers="h_%s"' % field)
        expected = ['f_radio', 'f_select', 'f_checkbox', 'f_textarea',
                    'f_text', 'reporter', 'owner']
        self.assertEqual(expected, sorted(positions, key=positions.get))
        for field in ('summary', 'description', 'type'):
            self.assertFalse(table.xpath('.//th[@id="h_%s"]' % field))
            self.assertFalse(table.xpath('.//*[@headers="h_%s"]' % field))

        self._test_script_data_in_query_page(
            {'fields': ['resolution', 'status', 'time', 'changetime',
                        'f_radio', 'f_select', 'f_checkbox', 'f_textarea',
                        'f_text', 'summary', 'reporter', 'owner',
                        'description', 'id'],
             'groups': {}})

    def test_grouped_fields(self):
        self.config.set('ticketfieldslayout', 'fields', '@_std,@_props,owner')
        self.config.set('ticketfieldslayout', 'group._std',
                        'summary,reporter,description')
        self.config.set('ticketfieldslayout', 'group._std.label', 'std')
        self.config.set('ticketfieldslayout', 'group._props',
                        'milestone,component,type,priority,version')
        self.config.set('ticketfieldslayout', 'group._props.label', 'props')
        self.config.set('ticketfieldslayout', 'group._props.collapsed',
                        'enabled')

        req = self._make_req('/newticket')
        content = self._render_ticket_page(req)
        parsed = self._parse_html(content)
        elements = parsed.xpath('.//fieldset[@id="properties"]')
        self.assertEqual(1, len(elements))
        fieldset = elements[0]

        fields = ['summary', 'reporter', 'description', 'milestone',
                  'component', 'type', 'priority', 'version']
        if self.has_owner_field:
            fields.append('owner')
        positions = {}
        for field in fields:
            self.assertTrue(fieldset.xpath('.//label[@for="field-%s"]' %
                                           field))
            self.assertTrue(fieldset.xpath('.//*[@name="field_%s"]' % field))
            positions[field] = content.index(' name="field_%s"' % field)
        self.assertEqual(fields, sorted(positions, key=positions.get))

        elements = fieldset.xpath('.//tbody')
        self.assertEqual(None, elements[0].attrib.get('class'))
        self.assertEqual('ticketfieldslayout-collapsed',
                         elements[1].attrib.get('class'))
        if self.has_owner_field:
            self.assertEqual(None, elements[2].attrib.get('class'))
            self.assertEqual(3, len(elements))
        else:
            self.assertEqual(2, len(elements))

        for field in ('keywords',):
            self.assertFalse(fieldset.xpath('.//label[@for="field-%s"]' %
                                            field))
            self.assertFalse(fieldset.xpath('.//*[@name="field_%s"]' % field))

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        content = self._render_ticket_page(req)
        parsed = self._parse_html(content)
        elements = parsed.xpath('.//table[@class="properties"]')
        self.assertEqual(1, len(elements))
        table = elements[0]

        fields = ['reporter', 'milestone', 'component', 'priority', 'version']
        if self.has_owner_field:
            fields.append('owner')
        positions = {}
        for field in fields:
            self.assertTrue(table.xpath('.//th[@id="h_%s"]' % field))
            self.assertTrue(table.xpath('.//*[@headers="h_%s"]' % field))
            positions[field] = content.index(' headers="h_%s"' % field)
        self.assertEqual(fields, sorted(positions, key=positions.get))
        for field in ('summary', 'description', 'type'):
            self.assertFalse(table.xpath('.//th[@id="h_%s"]' % field))
            self.assertFalse(table.xpath('.//*[@headers="h_%s"]' % field))

        elements = table.xpath('.//tbody')
        self.assertEqual(3, len(elements))
        self.assertEqual(None, elements[0].attrib.get('class'))
        self.assertEqual('ticketfieldslayout-collapsed',
                         elements[1].attrib.get('class'))
        self.assertEqual(None, elements[2].attrib.get('class'))

        self._test_script_data_in_query_page({
            'fields': ['resolution', 'status', 'time', 'changetime', '@_std',
                       '@_props', 'owner', 'id'],
            'groups': {
                '_std': {
                    'fields': ['summary','reporter','description'],
                    'collapsed': False, 'label': 'std', 'name': '_std',
                },
                '_props': {
                    'fields': ['milestone', 'component', 'type', 'priority',
                               'version'],
                    'collapsed': True, 'label': 'props', 'name': '_props',
                },
            },
        })

    def test_fullrow(self):
        self.config.set('ticket-custom', 'foo', 'textarea')
        tktsys = TicketSystem(self.env)
        self.config.set('ticketfieldslayout', 'fields',
                        ','.join(f['name'] for f in tktsys.fields))

        req = self._make_req('/newticket')
        content = self._render_ticket_page(req)
        parsed = self._parse_html(content)
        elements = parsed.xpath(
                            './/fieldset[@id="properties"]//td[@colspan="3"]')
        classes = [' '.join(sorted((element.attrib.get('class') or '')
                                   .split()))
                   for element in elements]

        if _parsed_version >= parse_version('1.4'):
            expected = ['col1 fullrow'] * 4
        elif _parsed_version >= parse_version('1.2'):
            expected = ['fullrow'] * 3 + ['col1 fullrow']
        else:
            expected = ['fullrow'] * 3 + ['col1']
        self.assertEqual(expected, classes)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketFieldsLayoutTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
