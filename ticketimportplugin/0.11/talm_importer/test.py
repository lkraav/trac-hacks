#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import difflib
import os.path
import pprint
import re
import shutil
import tempfile
import unittest
from genshi.core import Markup
from pkg_resources import parse_version

from trac import __version__ as VERSION
from trac.core import TracError
from trac.env import Environment
from trac.loader import load_components
from trac.test import EnvironmentStub
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.web.api import Request

from talm_importer.compat import get_read_db, with_transaction
from talm_importer.importer import ImportModule


if parse_version(VERSION) >= parse_version('0.12'):
    CTL_EXT = '-0.12.ctl'
else:
    CTL_EXT = '.ctl'


TOPDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTDIR = 'test'


def _db_query(db, stmt, *args):
    cursor = db.cursor()
    cursor.execute(stmt, args)
    return list(cursor)


def _printme(something):
    pass  # print something


class PrinterMarkupWrapper(object):
    def __init__(self, data):
        self.data = data

    _stringify_re = re.compile(r'\\.')

    def __repr__(self):
        def replace(match):
            val = match.group(0)
            if val == r'\n':
                return '\n'
            return val
        data = repr(self.data)[len("<Markup u'"):-len("'>")]
        return 'Markup(u"""\\\n' + self._stringify_re.sub(replace, data) + '""")'


class PrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, Markup):
            object = PrinterMarkupWrapper(object)
        elif isinstance(object, str):
            object = object.decode('utf-8')
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)


class ImporterBaseTestCase(unittest.TestCase):

    def setUp(self):
        self.TICKET_TIME = 1190909220
        self.env = EnvironmentStub(default_data=True)
        self._add_custom_field('mycustomfield', 'text', 'My Custom Field', '1')
        self.env.config.set('ticket', 'default_type', 'task')
        self.env.config.set('ticket', 'default_owner', '')
        @self.with_transaction
        def do_insert(db):
            cursor = db.cursor()
            cursor.executemany(
                "INSERT INTO permission VALUES ('anonymous',%s)",
                [('REPORT_ADMIN',), ('IMPORT_EXECUTE',)])
        self.mod = ImportModule(self.env)

    def tearDown(self):
        self.env.reset_db()

    def with_transaction(self, f):
        return with_transaction(self.env)(f)

    def _add_custom_field(self, name, type, label=None, order=None):
        self.env.config.set('ticket-custom', name, type)
        if label is not None:
            self.env.config.set('ticket-custom', name + '.label', label)
        if order is not None:
            self.env.config.set('ticket-custom', name + '.order', order)
        del TicketSystem(self.env).custom_fields

    def _remove_custom_fields(self):
        for name, value in self.env.config.options('ticket-custom'):
            self.env.config.remove('ticket-custom', name)

    def _pformat(self, data):
        return PrettyPrinter(indent=4).pformat(data)

    def _test_preview(self, filename):
        req = Request({'SERVER_PORT': 0, 'SERVER_NAME': 'any',
                       'wsgi.url_scheme': 'any', 'wsgi.input': 'any',
                       'REQUEST_METHOD': 'GET'}, lambda x, y: _printme)
        try:
           from trac.test import MockPerm
           req.perm = MockPerm()
        except ImportError:
           pass
        req.authname = 'testuser'
        #req.hdf = HDFWrapper([]) # replace by this if you want to generate HTML: req.hdf = HDFWrapper(loadpaths=chrome.get_all_templates_dirs())
        template, data, content_type = self.mod._do_preview(filename, 1, req, encoding='cp1252')
        #sys.stdout = tempstdout
        #req.display(template, content_type or 'text/html')
        #open('/tmp/out.html', 'w').write(req.hdf.render(template, None))
        return self._pformat(data)

    def _test_import(self, filename, sheet = 1):
        req = Request({'SERVER_PORT': 0, 'SERVER_NAME': 'any', 'wsgi.url_scheme': 'any', 'wsgi.input': 'any', 'REQUEST_METHOD': 'GET' }, lambda x, y: _printme)
        try:
           from trac.test import MockPerm
           req.perm = MockPerm()
        except ImportError:
           pass
        req.authname = 'testuser'
        #req.hdf = HDFWrapper([]) # replace by this if you want to generate HTML: req.hdf = HDFWrapper(loadpaths=chrome.get_all_templates_dirs())
        db = get_read_db(self.env)
        enums_before = _db_query(db, "SELECT * FROM enum")
        components_before = _db_query(db, "SELECT * FROM component")
        #print enums_before
        # when testing, always use the same time so that the results are comparable
        #print "importing " + filename + " with tickettime " + str(self.TICKET_TIME)
        template, data, content_type = \
            self.mod._do_import(filename, sheet, req, filename,
                                self.TICKET_TIME, encoding='cp1252')
        #sys.stdout = tempstdout
        #req.display(template, content_type or 'text/html')
        #open('/tmp/out.html', 'w').write(req.hdf.render(template, None))
        def empty2none(iterable):  # see trac:#11018
            def to_none(value):
                if value == '':
                    value = None
                return value
            return [tuple(to_none(value) for value in row) for row in iterable]
        tickets = empty2none(_db_query(db, "SELECT * FROM ticket ORDER BY id"))
        tickets_custom = empty2none(_db_query(
            db, "SELECT * FROM ticket_custom ORDER BY ticket, name"))
        tickets_change = empty2none(_db_query(
            db, "SELECT * FROM ticket_change"))
        enums = list(set(_db_query(db, "SELECT * FROM enum")) -
                     set(enums_before))
        components = list(set(_db_query(db, "SELECT * FROM component")) -
                          set(components_before))
        return self._pformat([tickets, tickets_custom, tickets_change, enums,
                              components])

    def _readfile(self, path):
        f = open(path, 'rb')
        try:
            return f.read()
        finally:
            f.close()

    def _writefile(self, path, data):
        f = open(path, 'wb')
        try:
            return f.write(data)
        finally:
            f.close()

    def _evalfile(self, path):
        contents = self._readfile(path)
        return eval(contents), contents

    def _do_test(self, filename, testfun):
        join = os.path.join
        outfilename = join(TESTDIR, filename + '.' + testfun.__name__ + '.out')
        ctlfilename = join(TESTDIR, filename + '.' + testfun.__name__ + CTL_EXT)
        self._writefile(outfilename, testfun(join(TESTDIR, filename)))
        outdata, outprint = self._evalfile(outfilename)
        ctldata, ctlprint = self._evalfile(ctlfilename)
        try:
            self.assertEquals(ctldata, outdata)
        except AssertionError:
            ctlprint = self._pformat(ctldata)
            diffs = list(difflib.ndiff(ctlprint.splitlines(),
                                       outprint.splitlines()))
            def contains_diff(diffs, idx, line):
                for diff in diffs[idx - line:idx + line]:
                    if not diff.startswith(' '):
                        return True
                return False
            raise AssertionError('Two objects do not match\n' +
                                 '\n'.join(diff.rstrip()
                                           for idx, diff in enumerate(diffs)
                                           if contains_diff(diffs, idx, 2)))

    def _do_test_diffs(self, filename, testfun):
        self._do_test(filename, testfun)

    def _do_test_with_exception(self, filename, testfun):
        try:
           self._do_test(filename, testfun)
        except TracError, e:
           return str(e)

    def _insert_ticket(self, id=None, type=None, time=None, changetime=None,
                       component=None, severity=None, priority=None,
                       owner=None, reporter=None, cc=None, version=None,
                       milestone=None, status=None, resolution=None,
                       summary=None, description=None, keywords=None):
        @self.with_transaction
        def do_insert(db):
            cursor = db.cursor()
            cursor.execute("""\
                INSERT INTO ticket VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                           %s,%s,%s,%s,%s)""",
                (id, type, time, changetime, component, severity, priority,
                 owner, reporter, cc, version, milestone, status, resolution,
                 summary, description, keywords))

    def _insert_one_ticket(self):
        self._insert_ticket(
            id=1245, type=u'defect', time=1191377630, changetime=1191377630,
            component=u'component1', priority=u'major', owner=u'somebody',
            reporter=u'anonymous', status=u'new', summary=u'sum2')


class ImporterTestCase(ImporterBaseTestCase):

    if hasattr(EnvironmentStub, 'insert_users'):
        def _insert_users(self, users):
            self.env.insert_users(users)
    else:
        def _insert_users(self, users):
            self.env.known_users.extend(users)

    def test_import_1(self):
        self._insert_one_ticket()
        self._do_test_diffs('Backlog-for-import.csv', self._test_preview)
        self._do_test_diffs('simple.csv', self._test_preview)
        self._do_test_diffs('simple.csv', self._test_preview)
        self._do_test('simple.csv', self._test_import)
        # Run again, to make sure that the lookups are done correctly
        self.TICKET_TIME = 1190909221
        self._do_test('simple-copy.csv', self._test_import)
        # import after modification should throw exception
        @self.with_transaction
        def do_update(db):
            cursor = db.cursor()
            cursor.execute("UPDATE ticket SET changetime=%s WHERE id=1245",
                           (self.TICKET_TIME + 10,))
        try:
           pass
           # TODO: this should throw an exception (a ticket has been modified between preview and import)
           #_do_test(env, 'simple-copy.csv', self._test_import)
        except TracError, err_string:
            print err_string
        #TODO: change the test case to modify the second or third row, to make sure that db.rollback() works

    def test_import_with_comments(self):
        self._insert_ticket(
            id=1245, type=u'defect', time=1191377630, changetime=1191377630,
            component=u'component1', priority=u'major', owner=u'somebody',
            reporter=u'anonymous', status=u'new', summary=u'sum2')
        self._do_test_diffs('simple.csv', self._test_import)
        self._do_test_diffs('simple_with_comments.csv', self._test_preview)
        self.TICKET_TIME = self.TICKET_TIME + 100
        self._do_test_diffs('simple_with_comments.csv', self._test_import)

    def test_import_with_comments_and_description(self):
        self._insert_ticket(
            id=1245, type=u'defect', time=1191377630, changetime=1191377630,
            component=u'component1', priority=u'major', owner=u'somebody',
            reporter=u'anonymous', status=u'new', summary=u'sum2')
        self._do_test_diffs('simple.csv', self._test_import)
        self._do_test_diffs('simple_with_comments_and_description.csv', self._test_preview)
        self.TICKET_TIME = self.TICKET_TIME + 100
        self._do_test_diffs('simple_with_comments_and_description.csv', self._test_import)


    def test_import_2(self):
        self._do_test_diffs('various-charsets.xls', self._test_preview)
        self._do_test('various-charsets.xls', self._test_import)

    def test_import_3(self):
        try:
           self._do_test_diffs('with-id.csv', self._test_preview)
           self.assert_(False)
        except TracError, e:
           self.assertEquals(str(e), 'Ticket 1 found in file, but not present in Trac: cannot import.')

    def test_import_4(self):
        @self.with_transaction
        def do_insert(db):
            self._insert_ticket(
                id=1, type=u'defect', time=1191377630, changetime=1191377630,
                component=u'component1', priority=u'major', owner=u'somebody',
                reporter=u'anonymous', status=u'new',
                summary=u'summary before change')
            self._insert_ticket(
                id=2, type=u'defect', time=1191377630, changetime=1191377630,
                component=u'component2', priority=u'major', owner=u'somebody2',
                reporter=u'anonymous2', status=u'new',
                summary=u'summarybefore change')
            cursor = db.cursor()
            cursor.executemany("INSERT INTO enum VALUES (%s,%s,%s)",
                               [('priority', 'mypriority', '1'),
                                ('priority', 'yourpriority', '2')])
            cursor.executemany("INSERT INTO component VALUES (%s,%s,%s)",
                               [('mycomp', '', ''), ('yourcomp', '', '')])
        self._do_test_diffs('with-id.csv', self._test_preview)
        self._do_test('with-id.csv', self._test_import)

    def test_import_5(self):
        @self.with_transaction
        def do_insert(db):
            self._insert_ticket(
                id=1, type=u'defect', time=1191377630, changetime=1191377630,
                component=u'component1', priority=u'major', owner=u'somebody',
                reporter=u'anonymous', status=u'new',
                summary=u'a summary that is duplicated')
            self._insert_ticket(
                id=2, type=u'defect', time=1191377630, changetime=1191377630,
                component=u'component2', priority=u'major', owner=u'somebody2',
                reporter=u'anonymous2', status=u'new',
                summary=u'a summary that is duplicated')
            self._insert_ticket(
                id=3, type=u'defect', time=1191377630, changetime=1191377630,
                component=u'component2', priority=u'major', owner=u'somebody2',
                reporter=u'anonymous2', status=u'new',
                summary=u'a summary that is duplicated')
        self.assertEquals(
            'Tickets #1, #2 and #3 have the same summary "a summary that is '
            'duplicated" in Trac. Ticket reconciliation by summary can not be '
            'done. Please modify the summaries to ensure that they are '
            'unique.',
            self._do_test_with_exception(
                'test-detect-duplicate-summary-in-trac.csv',
                self._test_preview))

    def test_import_6(self):
        self.assertEquals(
            'Summary "test & integration" is duplicated in the spreadsheet. '
            'Ticket reconciliation by summary can not be done. Please modify '
            'the summaries in the spreadsheet to ensure that they are unique.',
            self._do_test_with_exception(
                'test-detect-duplicate-summary-in-spreadsheet.csv',
                self._test_import))

    def test_import_7(self):
        if parse_version(VERSION) >= parse_version('0.12'):
            # Not working on 0.12, because of configuration reasons...
            return

        _dbfile = os.path.join(self.env.path, 'db', 'trac.db')
        os.remove(_dbfile)
        shutil.copyfile(os.path.join(TESTDIR, 'tickets.db'), _dbfile)
        self._remove_custom_fields()
        self._add_custom_field('domain', 'text', 'Domain')
        self._add_custom_field('stage', 'text', 'Stage')
        self._add_custom_field('users', 'text', 'Users')
        self.env.config.set('ticket', 'default_type', 'defect')
        self._do_test('ticket-13.xls', self._test_import)

    def test_import_with_ticket_types(self):
        self._do_test_diffs('simple-with-type.csv', self._test_preview)
        self._do_test_diffs('simple-with-type.csv', self._test_import)

    def test_import_with_reconciliation_by_owner(self):
        '''
        This test covers the two option flags "reconciliate_by_owner_also" and "skip_lines_with_empty_owner".
        '''
        self._remove_custom_fields()
        self._add_custom_field('effort', 'text', 'My Effort')
        self.env.config.set('importer', 'reconciliate_by_owner_also', 'true')
        self.env.config.set('importer', 'skip_lines_with_empty_owner', 'true')
        self._do_test('same-summary-different-owners-for-reconcilation-with-owner.xls', self._test_import)

    def test_import_csv_bug(self):
        '''
        This test covers the same as precedent, plus a problem I had with CSV:
        "TracError: Unable to read this file, does not seem to be a valid Excel or CSV file:newline inside string"
        The problem disapeared when I fixed the issue in test_import_with_reconciliation_by_owner
        '''
        self._remove_custom_fields()
        self._add_custom_field('effort', 'text', 'My Effort')
        self.env.config.set('importer', 'reconciliate_by_owner_also', 'true')
        self.env.config.set('importer', 'skip_lines_with_empty_owner', 'true')
        self._do_test('same-summary-different-owners-for-reconcilation-with-owner.csv', self._test_import)

    def test_import_not_first_worksheet(self):
        '''
        This test covers importing an index worksheet, plus a prb with an empty milestone:
  File "/Users/francois/workspace/importer/talm_importer/importer.py", line 416, in _process
    processor.process_new_lookups(newvalues)
  File "/Users/francois/workspace/importer/talm_importer/processors.py", line 128, in process_new_lookups
    lookup.insert()
  File "/sw/lib/python2.4/site-packages/Trac-0.11b1-py2.4.egg/trac/ticket/model.py", line 650, in insert
    assert self.name, 'Cannot create milestone with no name'
        '''
        self._remove_custom_fields()
        self._add_custom_field('effort', 'text', 'My Effort')
        self.env.config.set('importer', 'reconciliate_by_owner_also', 'true')
        self.env.config.set('importer', 'skip_lines_with_empty_owner', 'true')
        def _test_import_fourth_sheet(filename):
            return self._test_import(filename, 4)
        self._do_test('Backlog.xls', _test_import_fourth_sheet)

    def test_import_with_id_called_id(self):
        @self.with_transaction
        def do_insert(db):
            self._insert_ticket(
                id=1, type=u'defect', time=1191377630, changetime=1191377630,
                component=u'component1', priority=u'major', owner=u'somebody',
                reporter=u'anonymous', status=u'new',
                summary=u'summary before change')
            self._insert_ticket(
                id=2, type=u'defect', time=1191377630, changetime=1191377630,
                component=u'component2', priority=u'major', owner=u'somebody2',
                reporter=u'anonymous2', status=u'new',
                summary=u'summarybefore change')
            cursor = db.cursor()
            cursor.executemany("INSERT INTO enum VALUES (%s,%s,%s)",
                               [('priority', 'mypriority', '1'),
                                ('priority', 'yourpriority', '2')])
            cursor.executemany("INSERT INTO component VALUES (%s,%s,%s)",
                               [('mycomp', '', ''), ('yourcomp', '', '')])
        self._do_test_diffs('with-id-called-id.csv', self._test_preview)
        self._do_test('with-id-called-id.csv', self._test_import)

    def test_import_non_ascii_ticket_4458(self):
        self._do_test_diffs('non_ascii_ticket_4458.csv', self._test_preview)

    def test_ticket_6220(self):
        self._insert_users([('newuser2', None, None)])
        self._do_test_diffs('multiple_new_users_ticket_6220.csv', self._test_preview)

    def test_status_ticket_7679(self):
        self._do_test_diffs('importing_status_ticket_7679.csv', self._test_import)

    def test_project_ticket_7679(self):
        self._remove_custom_fields()
        self._add_custom_field('project', 'text', 'My Project')
        self._do_test_diffs('importing_project_ticket_7679.csv', self._test_import)

    def test_status_ticket_7658(self):
        self._do_test_diffs('importing_status_ticket_7658.csv', self._test_preview)
        self._do_test_diffs('importing_status_ticket_7658.csv', self._test_import)

    def test_preview_ticket_7205(self):
        self._do_test_diffs('simple_for_7205.csv', self._test_import)
        # preview after import... should now show any "modified-"
        self._do_test_diffs('simple_for_7205.csv', self._test_preview)

    def test_dates_ticket_8357(self):
        self._remove_custom_fields()
        self._add_custom_field('mydate', 'text', 'My Date')
        self._add_custom_field('mydatetime', 'text', 'My DateTime')
        self._do_test_diffs('datetimes.xls', self._test_preview)
        self._do_test_diffs('datetimes.xls', self._test_import)

    def test_dates_formatted_ticket_8357(self):
        self._remove_custom_fields()
        self._add_custom_field('mydate', 'text', 'My Date')
        self._add_custom_field('mydatetime', 'text', 'My DateTime')
        self.env.config.set('importer', 'datetime_format', '%x %X')
        self._do_test_diffs('datetimes_formatted.xls', self._test_preview)
        self._do_test_diffs('datetimes_formatted.xls', self._test_import)

    def test_celltypes_ticket_8804(self):
        self._remove_custom_fields()
        self.env.config.set('importer', 'datetime_format', '%Y-%m-%d %H:%M')
        self._do_test_diffs('celltypes-ticket-8804.xls', self._test_preview)
        self._do_test_diffs('celltypes-ticket-8804.xls', self._test_import)

    def test_restkey_ticket_9730(self):
        self._do_test_diffs('restkey_9730.csv', self._test_import)
        self._do_test_diffs('restkey_9730.csv', self._test_preview)

    def test_newticket_empty_status(self):
        self._do_test_diffs('newticket_empty_status.csv', self._test_preview)
        self._do_test_diffs('newticket_empty_status.csv', self._test_import)

    def test_empty_columns(self):
        self._do_test_diffs('empty_columns.csv', self._test_preview)
        self._do_test_diffs('empty_columns.csv', self._test_import)

    def test_ticket_refs(self):
        self._remove_custom_fields()
        self._add_custom_field('blockedby', 'text')
        self._add_custom_field('wbs', 'text')
        self._do_test_diffs('ticketrefs.csv', self._test_preview)
        # insert one ticket, so that the IDs are not trivially equal
        # to the row numbers when importing the ticket refs...
        self.TICKET_TIME = 1190909220
        self._insert_one_ticket()
        self._do_test_diffs('ticketrefs.csv', self._test_import)

    def test_ticket_refs_case(self):
        self._remove_custom_fields()
        self._add_custom_field('blockedby', 'text')
        self._add_custom_field('wbs', 'text')
        self._do_test_diffs('ticketrefs_case.csv', self._test_preview)
        # insert one ticket, so that the IDs are not trivially equal
        # to the row numbers when importing the ticket refs...
        self.TICKET_TIME = 1190909220
        self._insert_one_ticket()
        self._do_test_diffs('ticketrefs_case.csv', self._test_import)

    def test_ticket_refs_missing(self):
        # no custom fields...
        self._do_test_diffs('ticketrefs_missing.csv', self._test_preview)
        self._do_test_diffs('ticketrefs_missing_case.csv', self._test_preview)

    def test_handling_csv_error(self):
        try:
            self._do_test('test-handling-csv-error.csv',
                          self._test_preview)
            assert False, 'No TracError'
        except TracError, e:
            self.assertEquals('Error while reading from line 4 to 6',
                              unicode(e).split(':', 1)[0])


class MasterTicketsPluginTestCase(ImporterBaseTestCase):

    def setUp(self):
        self.TICKET_TIME = 1190909220
        path = tempfile.mkdtemp(prefix='ticketimportplugin-')
        plugin_dir = os.path.join(TOPDIR, 'test', 'eggs_10188')
        self.env = Environment(path, create=True)
        @self.with_transaction
        def do_insert(db):
            cursor = db.cursor()
            cursor.executemany(
                "INSERT INTO permission VALUES ('anonymous',%s)",
                [('REPORT_ADMIN',), ('IMPORT_EXECUTE',)])
        self.env.config.set('inherit', 'plugins_dir', plugin_dir)
        self.env.config.set('components', 'mastertickets.*', 'enabled')
        self._add_custom_field('mycustomfield', 'text', 'My Custom Field', '1')
        self._add_custom_field('blocking', 'text')
        self._add_custom_field('blockedby', 'text')
        self.env.config.set('ticket', 'default_type', 'task')
        self.env.config.set('ticket', 'default_owner', '')
        self.env.config.save()
        self.env.shutdown()
        self.env = Environment(path)
        load_components(self.env, [plugin_dir])
        self.env.upgrade()
        self.env.shutdown()
        self.env = Environment(path)
        self.mod = ImportModule(self.env)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    def _verify_mastertickets_table(self):
        db = get_read_db(self.env)
        cursor = db.cursor()
        cursor.execute('SELECT * FROM mastertickets')
        self.assertEquals([], list(cursor))

    def test_ticket_bug_10188(self): #FAILING
        self._verify_mastertickets_table()
        self._do_test_diffs('test_10188.xls', self._test_import)

    def test_10188(self): # FAILING
        self._verify_mastertickets_table()
        ticket = Ticket(self.env)
        ticket['summary'] = 'summary'
        ticket['blocking'] = ''
        ticket['blockedby'] = ''
        ticket.insert()
        ticket['blocking'] = ''
        ticket['blockedby'] = str(ticket.id)
        ticket.save_changes('someone','Some comments')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ImporterTestCase))
    if parse_version(VERSION) >= parse_version('0.12'):
        suite.addTest(unittest.makeSuite(MasterTicketsPluginTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
