# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from pkg_resources import parse_version
import io
import unittest

from trac import __version__ as VERSION
from trac.test import EnvironmentStub
from trac.ticket.model import Ticket
from trac.ticket.query import Query
from trac.ticket.report import ReportModule
from trac.util.datefmt import utc
from trac.web.api import RequestDone

from tracexceldownload.api import openpyxl, xlwt
from tracexceldownload.ticket import ExcelTicketModule, ExcelReportModule

try:
    from trac.test import MockRequest
except ImportError:
    from trac.test import Mock, MockPerm
    from trac.web.api import _RequestArgs, Request, arg_list_to_args
    from trac.web.chrome import Chrome

    def MockRequest(env, **kwargs):
        authname = kwargs.get('authname') or 'anonymous'

        def convert(val):
            if isinstance(val, bool):
                return unicode(int(val))
            elif isinstance(val, (long, int, float)):
                return unicode(val)
            elif isinstance(val, (list, tuple)):
                return [convert(v) for v in val]
            else:
                return val

        if 'arg_list' in kwargs:
            arg_list = [(k, convert(v)) for k, v in kwargs['arg_list']]
            args = arg_list_to_args(arg_list)
        else:
            args = _RequestArgs()
            args.update((k, convert(v))
                        for k, v in kwargs.get('args', {}).iteritems())
            arg_list = [(name, value) for name in args
                                      for value in args.getlist(name)]

        environ = {
            'trac.base_url': env.abs_href(),
            'wsgi.url_scheme': 'http',
            'HTTP_ACCEPT_LANGUAGE': kwargs.get('language', ''),
            'HTTP_COOKIE': kwargs.get('cookie', ''),
            'PATH_INFO': kwargs.get('path_info', '/'),
            'REQUEST_METHOD': kwargs.get('method', 'GET'),
            'REMOTE_ADDR': kwargs.get('remote_addr', '127.0.0.1'),
            'REMOTE_USER': kwargs.get('remote_user', authname),
            'SCRIPT_NAME': kwargs.get('script_name', '/trac.cgi'),
            'SERVER_NAME': kwargs.get('server_name', 'localhost'),
            'SERVER_PORT': kwargs.get('server_port', '80'),
        }
        for key in environ:
            if isinstance(environ[key], unicode):
                environ[key] = environ[key].encode('utf-8')

        status_sent = []
        headers_sent = {}
        response_sent = io.BytesIO()

        def start_response(status, headers, exc_info=None):
            status_sent.append(status)
            headers_sent.update(dict(headers))
            return response_sent.write

        req = Mock(Request, environ, start_response)
        req.status_sent = status_sent
        req.headers_sent = headers_sent
        req.response_sent = response_sent

        req.callbacks.update({
            'arg_list': lambda req: arg_list,
            'args': lambda req: args,
            'authname': lambda req: authname,
            'chrome': Chrome(env).prepare_request,
            'form_token': lambda req: kwargs.get('form_token', 0),
            'lc_time': lambda req: kwargs.get('lc_time'),
            'locale': lambda req: kwargs.get('locale'),
            'perm': lambda req: MockPerm(),
            'session': lambda req: {},
            'tz': lambda req: kwargs.get('tz', utc),
            'use_xsendfile': lambda req: False,
            'xsendfile_header': lambda req: None,
            'configurable_headers': lambda req: [],
        })

        return req


_has_time_fields = parse_version(VERSION) >= parse_version('1.2')


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
        if _has_time_fields:
            self.env.config.set('ticket-custom', 'col_time', 'time')
            self.env.config.set('ticket-custom', 'col_time.format', 'datetime')
        @self.env.with_transaction()
        def fn(db):
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
        template, data, content_type = report_mod.process_request(req)
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
