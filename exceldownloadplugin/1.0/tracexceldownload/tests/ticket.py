# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from pkg_resources import parse_version
import io
import sys
import unittest

from trac import __version__ as VERSION
from trac.test import EnvironmentStub, MockRequest
from trac.ticket.model import Ticket
from trac.ticket.query import Query
from trac.ticket.report import ReportModule
from trac.util.datefmt import utc
from trac.web.api import RequestDone

from ..api import openpyxl, xlwt
from ..ticket import ExcelTicketModule, ExcelReportModule


if sys.version_info[0] != 2:
    unichr = chr
    xrange = range
elif sys.maxunicode < 0x10000:
    _unichr = unichr
    def unichr(i):
        if i <= sys.maxunicode:
            return _unichr(i)
        else:
            return (br'U+%08x' % i).decode('unicode-escape')


_has_time_fields = parse_version(VERSION) >= parse_version('1.2')


def _text_from(iterable):
    return u''.join(map(unichr, iterable))


class AbstractExcelTicketTestCase(unittest.TestCase):

    _data_options = ['', 'foo', 'bar', 'baz', 'qux']
    _data_texts = [
        _text_from(xrange(256)),
        _text_from(xrange(0xff00, 0x10100)) +
        _text_from(xrange(0x5ff00, 0x60100)) +
        (u' \udfff\U0010fffd\U0010fffe\U0010ffff\ud800'
         u' \ud800\U0010fffd\U0010fffe\U0010ffff\udfff'
         if sys.maxunicode < 0x10000 else
         u'\U0010fffd\U0010fffe\U0010ffff'),
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
        if _has_time_fields:
            self.env.config.set('ticket-custom', 'col_time', 'time')
            self.env.config.set('ticket-custom', 'col_time.format', 'datetime')
        with self.env.db_transaction:
            for idx in xrange(20):
                idx += 1
                ticket = Ticket(self.env)
                ticket['summary'] = '=Summary %d' % idx
                ticket['status'] = 'new'
                ticket['milestone'] = 'milestone%d' % ((idx % 4) + 1)
                ticket['component'] = 'component%d' % ((idx % 2) + 1)
                ticket['col_text'] = texts[idx % len(texts)]
                ticket['col_checkbox'] = str(idx % 2)
                ticket['col_select'] = options[idx % len(options)]
                if _has_time_fields:
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
        self.assertNotIsInstance(content, bytes)
        content = b''.join(content)
        self.assertEqual(self._magic_number, content[:8])
        self.assertEqual(self._mimetype, mimetype)
        book = self._read_workbook(content)
        if book:
            self.assertEqual(['Change History'], book['names'])

    def test_query(self):
        mod = ExcelTicketModule(self.env)
        req = MockRequest(self.env)
        query = Query.from_string(self.env, 'status=!closed&order=id&max=9')
        content, mimetype = mod.convert_content(req, self._mimetype, query,
                                                'excel')
        self.assertNotIsInstance(content, bytes)
        content = b''.join(content)
        self.assertEqual(self._magic_number, content[:8])
        self.assertEqual(self._mimetype, mimetype)
        book = self._read_workbook(content)
        if book:
            self.assertEqual(['Custom Query'], book['names'])
            cells = book['sheets'][0]
            self.assertEqual('Custom Query (20 matches)', cells[0][0])
            self.assertEqual('Ticket', cells[1][0])
            self.assertEqual('Summary', cells[1][1])
            self.assertEqual('#1', cells[2][0])
            self.assertEqual('=Summary 1', cells[2][1])
            self.assertEqual('#9', cells[10][0])
            self.assertEqual('=Summary 9', cells[10][1])

        content, mimetype = mod.convert_content(req, self._mimetype, query,
                                                'excel-history')
        self.assertNotIsInstance(content, bytes)
        content = b''.join(content)
        self.assertEqual(self._magic_number, content[:8])
        self.assertEqual(self._mimetype, mimetype)
        book = self._read_workbook(content)
        if book:
            self.assertEqual(['Custom Query', 'Change History'], book['names'])

    def test_report(self):
        mod = ExcelReportModule(self.env)
        req = MockRequest(self.env, path_info='/report/1',
                          args={'id': '1', 'format': 'xls'})
        report_mod = ReportModule(self.env)
        self.assertTrue(report_mod.match_request(req))
        rv = report_mod.process_request(req)
        template, data = rv[:2]
        content_type = rv[2] if len(rv) == 3 else None
        self.assertEqual('report_view.html', template)
        try:
            mod.post_process_request(req, template, data, content_type)
            self.fail('not raising RequestDone')
        except RequestDone:
            content = req.response_sent.getvalue()
        self.assertEqual(self._magic_number, content[:8])
        self.assertEqual(self._mimetype, req.headers_sent['Content-Type'])
        book = self._read_workbook(content)
        if book:
            self.assertEqual(['Report'], book['names'])

    def _read_workbook(self, content):
        raise NotImplementedError


class Excel2003TicketTestCase(AbstractExcelTicketTestCase):

    _format = 'xls'
    _mimetype = 'application/vnd.ms-excel'
    _magic_number = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'

    def _read_workbook(self, content):
        import xlrd
        book = xlrd.open_workbook(file_contents=content)
        sheets = list(book.sheets())
        rv = {}
        rv['names'] = [s.name for s in sheets]
        rv['sheets'] = [[[c.value for c in r] for r in s.get_rows()]
                        for s in sheets]
        return rv


class Excel2007TicketTestCase(AbstractExcelTicketTestCase):

    _format = 'xlsx'
    _mimetype = 'application/' \
                'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    _magic_number = b'PK\x03\x04\x14\x00\x00\x00'

    def _read_workbook(self, content):
        rv = {}
        with io.BytesIO(content) as f:
            book = openpyxl.load_workbook(f, read_only=True, data_only=True)
            rv['names'] = book.sheetnames
            rv['sheets'] = [[[c.value for c in row] for row in s.iter_rows()]
                            for s in book.worksheets]
            book.close()
        return rv


def suite():
    suite = unittest.TestSuite()
    if not xlwt and not openpyxl:
        raise AssertionError('xlwt or openpyxl should be available')
    if xlwt:
        suite.addTest(unittest.makeSuite(Excel2003TicketTestCase))
    if openpyxl:
        suite.addTest(unittest.makeSuite(Excel2007TicketTestCase))
    return suite
