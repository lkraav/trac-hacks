# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2023 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from trac.admin.web_ui import AdminModule
from trac.test import EnvironmentStub, MockRequest
from trac.ticket.api import TicketSystem
from trac.web.api import RequestDone
from tracticketfieldslayout.admin import TicketFieldsLayoutAdminModule


class CustomFieldsModificationTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.config = self.env.config

    def tearDown(self):
        self.env.reset_db()

    def _make_req(self, method='POST', path_info='/admin/ticket/customfields'):
        return MockRequest(self.env, method=method, path_info=path_info)

    def _pseudo_process_request(self, fn):
        handler = AdminModule(self.env)
        mod = TicketFieldsLayoutAdminModule(self.env)
        req = self._make_req()
        self.assertTrue(handler.match_request(req))
        mod.pre_process_request(req, handler)
        fn()
        self.config.save()
        del TicketSystem(self.env).custom_fields
        try:
            req.redirect('/')
        except RequestDone:
            pass

    def test_add_to_fields(self):
        def fn():
            self.config.set('ticket-custom', 'blah1', 'text')
            self.config.set('ticket-custom', 'blah1.order', '2')
            self.config.set('ticket-custom', 'blah2', 'textarea')
            self.config.set('ticket-custom', 'blah2.order', '1')
        self.config.set('ticketfieldslayout', 'fields',
                        'summary,reporter,owner,description')
        self._pseudo_process_request(fn)
        self.assertEqual('summary,reporter,owner,description,blah2,blah1',
                         self.config.get('ticketfieldslayout', 'fields'))

    def test_add_to_fields_if_not_configured(self):
        def fn():
            self.config.set('ticket-custom', 'blah', 'text')
        self.config.set('ticketfieldslayout', 'fields', '')
        self._pseudo_process_request(fn)
        self.assertEqual('', self.config.get('ticketfieldslayout', 'fields'))

    def test_remove_from_fields(self):
        def fn():
            self.config.remove('ticket-custom', 'blah1')
            self.config.remove('ticket-custom', 'blah3')
        self.config.set('ticketfieldslayout', 'fields',
                        'summary,reporter,owner,blah1,blah2,blah3,description')
        self.config.set('ticket-custom', 'blah1', 'text')
        self.config.set('ticket-custom', 'blah2', 'text')
        self.config.set('ticket-custom', 'blah3', 'text')
        self._pseudo_process_request(fn)
        self.assertEqual('summary,reporter,owner,blah2,description',
                         self.config.get('ticketfieldslayout', 'fields'))

    def test_remove_from_group(self):
        def fn():
            self.config.remove('ticket-custom', 'blah1')
            self.config.remove('ticket-custom', 'blah2')
        self.config.set('ticketfieldslayout', 'fields',
                        'summary,reporter,owner,@_opt,description')
        self.config.set('ticketfieldslayout', 'group._opt',
                        'blah1,blah2,blah3')
        self.config.set('ticketfieldslayout', 'group._opt.label', 'Optional')
        self.config.set('ticket-custom', 'blah1', 'text')
        self.config.set('ticket-custom', 'blah2', 'text')
        self.config.set('ticket-custom', 'blah3', 'text')
        self._pseudo_process_request(fn)
        self.assertEqual('summary,reporter,owner,@_opt,description',
                         self.config.get('ticketfieldslayout', 'fields'))
        self.assertEqual('blah3', self.config.get('ticketfieldslayout',
                                             'group._opt'))

    def test_remove_all_fields_from_group(self):
        def fn():
            self.config.remove('ticket-custom', 'blah1')
            self.config.remove('ticket-custom', 'blah2')
            self.config.remove('ticket-custom', 'blah3')
        self.config.set('ticketfieldslayout', 'fields',
                        'summary,reporter,owner,@_opt,description')
        self.config.set('ticketfieldslayout', 'group._opt',
                        'blah1,blah2,blah3')
        self.config.set('ticketfieldslayout', 'group._opt.label', 'Optional')
        self.config.set('ticket-custom', 'blah1', 'text')
        self.config.set('ticket-custom', 'blah2', 'text')
        self.config.set('ticket-custom', 'blah3', 'text')
        self._pseudo_process_request(fn)
        self.assertEqual('summary,reporter,owner,description',
                         self.config.get('ticketfieldslayout', 'fields'))
        self.assertEqual('', self.config.get('ticketfieldslayout',
                                             'group._opt'))

    def test_remove_unused_fields(self):
        def fn():
            self.config.remove('ticket-custom', 'blah1')
        self.config.set('ticketfieldslayout', 'fields',
                        'summary,reporter,owner,@_opt,description')
        self.config.set('ticketfieldslayout', 'group._opt',
                        'blah3')
        self.config.set('ticketfieldslayout', 'group._opt.label', 'Optional')
        self.config.set('ticket-custom', 'blah1', 'text')
        self.config.set('ticket-custom', 'blah2', 'text')
        self.config.set('ticket-custom', 'blah3', 'text')
        self._pseudo_process_request(fn)
        self.assertEqual('summary,reporter,owner,@_opt,description',
                         self.config.get('ticketfieldslayout', 'fields'))
        self.assertEqual('blah3', self.config.get('ticketfieldslayout',
                                                  'group._opt'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CustomFieldsModificationTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
