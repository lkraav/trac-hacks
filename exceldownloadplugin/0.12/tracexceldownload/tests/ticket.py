# -*- coding: utf-8 -*-

import unittest

from trac.test import EnvironmentStub, MockRequest
from trac.ticket.model import Ticket
from trac.ticket.query import Query
from trac.ticket.report import ReportModule
from trac.web.api import RequestDone

from tracexceldownload.ticket import ExcelTicketModule, ExcelReportModule


class ExcelTicketTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True)
        @self.env.with_transaction()
        def fn(db):
            for idx in xrange(20):
                idx += 1
                ticket = Ticket(self.env)
                ticket['summary'] = 'Summary %d' % idx
                ticket['status'] = 'new'
                ticket['milestone'] = 'milestone%d' % ((idx % 4) + 1)
                ticket['component'] = 'component%d' % ((idx % 2) + 1)
                ticket.insert()

    def tearDown(self):
        self.env.reset_db()

    def test_ticket(self):
        mod = ExcelTicketModule(self.env)
        req = MockRequest(self.env)
        ticket = Ticket(self.env, 11)
        content, mimetype = mod.convert_content(
            req, 'application/vnd.ms-excel', ticket, 'excel-history')
        self.assertEqual('\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', content[:8])
        self.assertEqual('application/vnd.ms-excel', mimetype)

    def test_query(self):
        mod = ExcelTicketModule(self.env)
        req = MockRequest(self.env)
        query = Query.from_string(self.env, 'status=!closed&max=9')
        content, mimetype = mod.convert_content(
            req, 'application/vnd.ms-excel', query, 'excel')
        self.assertEqual('\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', content[:8])
        self.assertEqual('application/vnd.ms-excel', mimetype)
        content, mimetype = mod.convert_content(
            req, 'application/vnd.ms-excel', query, 'excel-history')
        self.assertEqual('\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', content[:8])
        self.assertEqual('application/vnd.ms-excel', mimetype)

    def test_report(self):
        mod = ExcelReportModule(self.env)
        req = MockRequest(self.env, path_info='/report/1',
                          args={'id': '1', 'format': 'xls'})
        report_mod = ReportModule(self.env)
        self.assertTrue(report_mod.match_request(req))
        template, data, content_type = report_mod.process_request(req)
        self.assertEqual('report_view.html', template)
        try:
            mod.post_process_request(req, template, data, content_type)
            self.fail('not raising RequestDone')
        except RequestDone:
            content = req.response_sent.getvalue()
            self.assertEqual('\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
                             content[:8])
            self.assertEqual('application/vnd.ms-excel',
                             req.headers_sent['Content-Type'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExcelTicketTestCase))
    return suite
