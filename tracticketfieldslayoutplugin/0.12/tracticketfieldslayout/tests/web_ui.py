# -*- coding: utf-8 -*-
#
# Copyright (C) 2013,2014 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest
from cStringIO import StringIO
from genshi import XML
from genshi.core import START
from pkg_resources import parse_version

from trac import __version__
from trac.test import EnvironmentStub, MockPerm
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.ticket.query import QueryModule
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import utc
from trac.web.api import Request
from trac.web.chrome import Chrome
from trac.web.main import FakeSession
from tracticketfieldslayout.web_ui import TicketFieldsLayoutModule


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
                              enable=['trac.*', TicketFieldsLayoutModule])
        self.env = env
        self.config = env.config
        self.mod = TicketFieldsLayoutModule(env)
        self.tktmod = TicketModule(env)
        self.querymod = QueryModule(env)

    def tearDown(self):
        self.env.reset_db()

    def _create_ticket(self, **kwargs):
        ticket = Ticket(self.env)
        for name, value in kwargs.iteritems():
            ticket[name] = value
        ticket.insert()
        return ticket

    def _reset_ticket_fields(self):
        TicketSystem(self.env).reset_ticket_fields()

    def _make_environ(self, scheme='http', server_name='example.org',
                      server_port=80, method='GET', script_name='/trac',
                      **kwargs):
        environ = {'wsgi.url_scheme': scheme, 'wsgi.input': StringIO(''),
                   'REQUEST_METHOD': method, 'SERVER_NAME': server_name,
                   'SERVER_PORT': server_port, 'SCRIPT_NAME': script_name}
        environ.update(kwargs)
        return environ

    def _make_req(self, path_info=None):
        buf = StringIO()
        def start_response(status, headers):
            return buf.write
        environ = self._make_environ(PATH_INFO=path_info)
        req = Request(environ, start_response)
        req.authname = 'anonymous'
        req.perm = MockPerm()
        req.session = FakeSession()
        req.chrome = {}
        req.tz = utc
        req.locale = None
        req.lc_time = 'iso8601'
        req.form_token = None
        return req

    def _process_request(self, req, mod):
        self.assertTrue(mod.match_request(req))
        return mod.process_request(req)

    def _render(self, req, mod):
        template, data, content_type = self._process_request(req, mod)
        return Chrome(self.env).render_template(req, template, data,
                                                content_type, fragment=True)

    def _render_ticket_page(self, req):
        return self._render(req, self.tktmod)

    def _test_script_data_in_query_page(self, ticketfieldslayout):
        req = self._make_req('/query')
        template, data, content_type = self._process_request(req, self.querymod)
        self.mod.post_process_request(req, template, data, content_type)
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
        stream = self._render_ticket_page(req)
        stream = stream.select('//fieldset[@id="properties"]')
        content = unicode(stream)

        positions = []
        for field in self.hidden_fields:
            self.assertIn('<label for="field-%s">' % field, content)
            self.assertIn(' name="field_%s"' % field, content)
            positions.append((content.index(' name="field_%s"' % field),
                              field))
        self.assertEqual(self.hidden_fields,
                         tuple(map(lambda v: v[1], sorted(positions))))

        XML(content)  # try to parse as an xml
        for field in ('type', 'priority', 'milestone', 'component', 'version',
                      'keywords'):
            self.assertNotIn('<label for="field-%s">' % field, content)
            self.assertNotIn('name="field_%s"' % field, content)

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        stream = self._render_ticket_page(req)
        stream = stream.select('//table[@class="properties"]')
        content = unicode(stream)

        positions = []
        for field in ('reporter', 'owner'):
            self.assertIn('<th id="h_%s"' % field, content)
            self.assertIn(' headers="h_%s"' % field, content)
            positions.append((content.index(' headers="h_%s"' % field),
                              field))
        self.assertEqual(['reporter', 'owner'],
                         map(lambda v: v[1], sorted(positions)))
        for field in ('summary', 'description', 'type'):
            self.assertNotIn('<th id="h_%s"' % field, content)
            self.assertNotIn(' headers="h_%s"' % field, content)

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
        stream = self._render_ticket_page(req)
        stream = stream.select('//fieldset[@id="properties"]')
        content = unicode(stream)

        positions = []
        for field in fields:
            if field == 'owner' and not self.has_owner_field:
                continue
            if field != 'f_radio':
                self.assertIn('<label for="field-%s">' % field, content)
            self.assertIn(' name="field_%s"' % field, content)
            positions.append((content.index(' name="field_%s"' % field),
                              field))
        expected = ['f_radio', 'f_select', 'f_checkbox', 'f_textarea',
                    'f_text', 'summary', 'reporter', 'description']
        if self.has_owner_field:
            expected.append('owner')
        self.assertEqual(expected, map(lambda v: v[1], sorted(positions)))

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        stream = self._render_ticket_page(req)
        stream = stream.select('//table[@class="properties"]')
        content = unicode(stream)

        positions = []
        for field in set(fields) - set(('summary', 'description')):
            self.assertIn('<th id="h_%s"' % field, content)
            self.assertIn(' headers="h_%s"' % field, content)
            positions.append((content.index(' headers="h_%s"' % field),
                              field))
        expected = ['f_radio', 'f_select', 'f_checkbox', 'f_textarea',
                    'f_text', 'reporter', 'owner']
        self.assertEqual(expected, map(lambda v: v[1], sorted(positions)))
        for field in ('summary', 'description', 'type'):
            self.assertNotIn('<th id="h_%s"' % field, content)
            self.assertNotIn(' headers="h_%s"' % field, content)

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
        stream = self._render_ticket_page(req)
        stream = stream.select('//fieldset[@id="properties"]')
        content = unicode(stream)

        fields = ['summary', 'reporter', 'description', 'milestone',
                  'component', 'type', 'priority', 'version']
        if self.has_owner_field:
            fields.append('owner')
        positions = []
        for field in fields:
            self.assertIn('<label for="field-%s">' % field, content)
            self.assertIn(' name="field_%s"' % field, content)
            positions.append((content.index(' name="field_%s"' % field),
                              field))
        self.assertEqual(fields, map(lambda v: v[1], sorted(positions)))

        tbody = filter(lambda (kind, data, pos): \
                       (kind is START and data[0].localname == 'tbody'),
                       XML(content).select('//tbody'))
        self.assertEqual(None, tbody[0][1][1].get('class'))
        self.assertEqual('ticketfieldslayout-collapsed',
                         tbody[1][1][1].get('class'))
        if self.has_owner_field:
            self.assertEqual(None, tbody[2][1][1].get('class'))
            self.assertEqual(3, len(tbody))
        else:
            self.assertEqual(2, len(tbody))

        XML(content)  # try to parse as an xml
        for field in ('keywords',):
            self.assertNotIn('<label for="field-%s">' % field, content)
            self.assertNotIn('name="field_%s"' % field, content)

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        stream = self._render_ticket_page(req)
        stream = stream.select('//table[@class="properties"]')
        content = unicode(stream)

        fields = ['reporter', 'milestone', 'component', 'priority', 'version']
        if self.has_owner_field:
            fields.append('owner')
        positions = []
        for field in fields:
            self.assertIn('<th id="h_%s"' % field, content)
            self.assertIn(' headers="h_%s"' % field, content)
            positions.append((content.index(' headers="h_%s"' % field),
                              field))
        self.assertEqual(fields, map(lambda v: v[1], sorted(positions)))
        for field in ('summary', 'description', 'type'):
            self.assertNotIn('<th id="h_%s"' % field, content)
            self.assertNotIn(' headers="h_%s"' % field, content)

        tbody = filter(lambda (kind, data, pos): \
                       (kind is START and data[0].localname == 'tbody'),
                       XML(content).select('//tbody'))
        self.assertEqual(None, tbody[0][1][1].get('class'))
        self.assertEqual('ticketfieldslayout-collapsed',
                         tbody[1][1][1].get('class'))
        self.assertEqual(None, tbody[2][1][1].get('class'))
        self.assertEqual(3, len(tbody))

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
        stream = self._render_ticket_page(req)
        classes = [' '.join(sorted(data[1].get('class').split()))
                   for kind, data, pos
                   in stream.select('//fieldset[@id="properties"]'
                                    '//td[@colspan="3"]')
                   if kind is START and data[0].localname == 'td']

        self.assertEqual(['fullrow'] * 3, classes[:3])
        expected = 'col1' if _parsed_version < parse_version('1.2') else \
                   'col1 fullrow'
        self.assertEqual(expected, classes[3])
        self.assertEqual(4, len(classes))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketFieldsLayoutTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
