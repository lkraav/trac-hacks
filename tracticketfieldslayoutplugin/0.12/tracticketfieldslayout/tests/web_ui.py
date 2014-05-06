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

from trac.test import EnvironmentStub, MockPerm
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import utc
from trac.web.api import Request
from trac.web.chrome import Chrome
from tracticketfieldslayout.web_ui import TicketFieldsLayoutModule


class TicketFieldsLayoutTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', TicketFieldsLayoutModule])
        self.req = self._make_req()
        self.mod = TicketModule(self.env)

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
        req.session = {}
        req.chrome = {}
        req.tz = utc
        req.locale = None
        req.lc_time = 'iso8601'
        req.form_token = None
        return req

    def _render(self, req):
        self.assertTrue(self.mod.match_request(req))
        template, data, content_type = self.mod.process_request(req)
        return Chrome(self.env).render_template(req, template, data,
                                                content_type, fragment=True)

    if not hasattr(unittest.TestCase, 'assertIn'):
        def assertIn(self, first, second, msg=None):
            if first not in second:
                self.fail(msg or '%r not in %r' % (first, second))

    if not hasattr(unittest.TestCase, 'assertNotIn'):
        def assertNotIn(self, first, second, msg=None):
            if first in second:
                self.fail(msg or '%r in %r' % (first, second))

    def test_hidden_fields(self):
        self.env.config.set('ticketfieldslayout', 'fields',
                            'summary,reporter,owner,description')

        req = self._make_req('/newticket')
        stream = self._render(req)
        stream = stream.select('//fieldset[@id="properties"]')
        content = unicode(stream)

        positions = []
        for field in ('summary', 'reporter', 'owner', 'description'):
            self.assertIn('<label for="field-%s">' % field, content)
            self.assertIn(' name="field_%s"' % field, content)
            positions.append((content.index(' name="field_%s"' % field),
                              field))
        self.assertEqual(['summary', 'reporter', 'description', 'owner'],
                         map(lambda v: v[1], sorted(positions)))

        xhtml = XML(content)
        for field in ('type', 'priority', 'milestone', 'component', 'version',
                      'keywords'):
            self.assertNotIn('<label for="field-%s">' % field, content)
            self.assertNotIn('name="field_%s"' % field, content)

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        stream = self._render(req)
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

    def test_custom_fields(self):
        fields = ('f_radio', 'f_select', 'f_checkbox', 'f_textarea', 'f_text',
                  'summary', 'reporter', 'owner', 'description')
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
            self.env.config.set('ticket-custom', name, value)
        self.env.config.set('ticketfieldslayout', 'fields', ','.join(fields))

        req = self._make_req('/newticket')
        stream = self._render(req)
        stream = stream.select('//fieldset[@id="properties"]')
        content = unicode(stream)

        positions = []
        for field in fields:
            if field != 'f_radio':
                self.assertIn('<label for="field-%s">' % field, content)
            self.assertIn(' name="field_%s"' % field, content)
            positions.append((content.index(' name="field_%s"' % field),
                              field))
        self.assertEqual(['f_radio', 'f_select', 'f_checkbox', 'f_textarea',
                          'f_text', 'summary', 'reporter', 'description',
                          'owner'],
                          map(lambda v: v[1], sorted(positions)))

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        stream = self._render(req)
        stream = stream.select('//table[@class="properties"]')
        content = unicode(stream)

        positions = []
        for field in set(fields) - set(('summary', 'description')):
            self.assertIn('<th id="h_%s"' % field, content)
            self.assertIn(' headers="h_%s"' % field, content)
            positions.append((content.index(' headers="h_%s"' % field),
                              field))
        self.assertEqual(['f_radio', 'f_select', 'f_checkbox', 'f_textarea',
                          'f_text', 'reporter', 'owner'],
                         map(lambda v: v[1], sorted(positions)))
        for field in ('summary', 'description', 'type'):
            self.assertNotIn('<th id="h_%s"' % field, content)
            self.assertNotIn(' headers="h_%s"' % field, content)

    def test_grouped_fields(self):
        self.env.config.set('ticketfieldslayout', 'fields', '@_std,@_props,owner')
        self.env.config.set('ticketfieldslayout', 'group._std',
                            'summary,reporter,description')
        self.env.config.set('ticketfieldslayout', 'group._props',
                            'milestone,component,type,priority,version')
        self.env.config.set('ticketfieldslayout', 'group._props.collapsed',
                            'enabled')

        req = self._make_req('/newticket')
        stream = self._render(req)
        stream = stream.select('//fieldset[@id="properties"]')
        content = unicode(stream)

        positions = []
        for field in ('summary', 'reporter', 'owner', 'description', 'type',
                      'priority', 'milestone', 'component', 'version'):
            self.assertIn('<label for="field-%s">' % field, content)
            self.assertIn(' name="field_%s"' % field, content)
            positions.append((content.index(' name="field_%s"' % field),
                              field))
        self.assertEqual(['summary', 'reporter', 'description', 'milestone',
                          'component', 'type', 'priority', 'version', 'owner'],
                         map(lambda v: v[1], sorted(positions)))

        tbody = filter(lambda (kind, data, pos): \
                       (kind is START and data[0].localname == 'tbody'),
                       XML(content).select('//tbody'))
        self.assertEqual(None, tbody[0][1][1].get('class'))
        self.assertEqual('ticketfieldslayout-collapsed',
                         tbody[1][1][1].get('class'))
        self.assertEqual(None, tbody[2][1][1].get('class'))
        self.assertEqual(3, len(tbody))

        xhtml = XML(content)
        for field in ('keywords',):
            self.assertNotIn('<label for="field-%s">' % field, content)
            self.assertNotIn('name="field_%s"' % field, content)

        ticket = self._create_ticket(summary='Layout', status='new')
        req = self._make_req('/ticket/%d' % ticket.id)
        stream = self._render(req)
        stream = stream.select('//table[@class="properties"]')
        content = unicode(stream)

        positions = []
        for field in ('reporter', 'owner', 'priority', 'milestone',
                      'component', 'version'):
            self.assertIn('<th id="h_%s"' % field, content)
            self.assertIn(' headers="h_%s"' % field, content)
            positions.append((content.index(' headers="h_%s"' % field),
                              field))
        self.assertEqual(['reporter', 'milestone', 'component', 'priority',
                          'version', 'owner'],
                         map(lambda v: v[1], sorted(positions)))
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketFieldsLayoutTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
