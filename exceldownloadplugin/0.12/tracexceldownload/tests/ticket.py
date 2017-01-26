# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import unittest

from trac.test import EnvironmentStub, MockRequest
from trac.ticket.model import Ticket
from trac.ticket.query import Query
from trac.ticket.report import ReportModule
from trac.util.datefmt import utc
from trac.web.api import RequestDone

from tracexceldownload.ticket import ExcelTicketModule, ExcelReportModule


class AbstractExcelTicketTestCase(unittest.TestCase):

    _data_options = ['', 'foo', 'bar', 'baz', 'qux']
    _data_texts = [
        ''.join(map(unichr, xrange(256))),
        ''.join(map(unichr, xrange(0xff00, 0x10100))),
    ]

    def setUp(self):
        options = self._data_options
        texts = self._data_texts

        self.env = EnvironmentStub(default_data=True)
        self.env.config.set('exceldownload', 'format', self._format)
        self.env.config.set('ticket-custom', 'col_text', 'text')
        self.env.config.set('ticket-custom', 'col_checkbox', 'checkbox')
        self.env.config.set('ticket-custom', 'col_select', 'select')
        self.env.config.set('ticket-custom', 'col_select.options',
                            '|'.join(options))
        self.env.config.set('ticket-custom', 'col_time', 'time')
        self.env.config.set('ticket-custom', 'col_time.format', 'datetime')
        @self.env.with_transaction()
        def fn(db):
            for idx in xrange(20):
                idx += 1
                ticket = Ticket(self.env)
                ticket['summary'] = 'Summary %d' % idx
                ticket['status'] = 'new'
                ticket['milestone'] = 'milestone%d' % ((idx % 4) + 1)
                ticket['component'] = 'component%d' % ((idx % 2) + 1)
                ticket['col_text'] = texts[idx % len(texts)]
                ticket['col_checkbox'] = str(idx % 2)
                ticket['col_select'] = options[idx % len(options)]
                ticket['col_time'] = \
                    datetime(2016, 12, 31, 13, 45, 59, 98765, utc) + \
                    timedelta(days=idx, seconds=idx * 2)
                ticket.insert()

    def tearDown(self):
        self.env.reset_db()

    def test_ticket(self):
        mod = ExcelTicketModule(self.env)
        req = MockRequest(self.env)
        ticket = Ticket(self.env, 11)
        content, mimetype = mod.convert_content(req, self._mimetype, ticket,
                                                'excel-history')
        self.assertEqual(self._magic_number, content[:8])
        self.assertEqual(self._mimetype, mimetype)

    def test_query(self):
        mod = ExcelTicketModule(self.env)
        req = MockRequest(self.env)
        query = Query.from_string(self.env, 'status=!closed&max=9')
        content, mimetype = mod.convert_content(req, self._mimetype, query,
                                                'excel')
        self.assertEqual(self._magic_number, content[:8])
        self.assertEqual(self._mimetype, mimetype)
        content, mimetype = mod.convert_content(req, self._mimetype, query,
                                                'excel-history')
        self.assertEqual(self._magic_number, content[:8])
        self.assertEqual(self._mimetype, mimetype)

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
            self.assertEqual(self._magic_number, content[:8])
            self.assertEqual(self._mimetype, req.headers_sent['Content-Type'])


class Excel2003TicketTestCase(AbstractExcelTicketTestCase):

    _format = 'xls'
    _mimetype = 'application/vnd.ms-excel'
    _magic_number = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


class Excel2007TicketTestCase(AbstractExcelTicketTestCase):

    _format = 'xlsx'
    _mimetype = 'application/' \
                'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    _magic_number = b'PK\x03\x04\x14\x00\x00\x00'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Excel2003TicketTestCase))
    suite.addTest(unittest.makeSuite(Excel2007TicketTestCase))
    return suite
