# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from __future__ import with_statement

import inspect
import os
import pkg_resources
import tempfile
import unittest
from cStringIO import StringIO
from datetime import datetime

from trac.attachment import Attachment
from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock
from trac.ticket.api import TicketSystem
from trac.ticket.model import Milestone, Ticket
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc
from trac.versioncontrol.api import (
    DbRepositoryProvider, IRepositoryConnector, Repository, RepositoryManager)
from trac.versioncontrol.cache import CachedRepository
from trac.wiki.admin import WikiAdmin
from trac.wiki.model import WikiPage

from tracbacklink import db_default
from tracbacklink.api import (MockRequest, TracBackLinkChangeset as Changeset,
                              TracBackLinkSystem, gather_links)


if 'remote_addr' in inspect.getargspec(WikiPage.save)[0]:
    def _save_page(page, author, comment):
        page.save(author, comment, remote_addr='::1')
else:
    def _save_page(page, author, comment):
        page.save(author, comment)


class RepositoryStubConnector(Component):

    implements(IRepositoryConnector)

    def get_supported_types(self):
        yield 'stub', 1

    def get_repository(self, repos_type, repos_dir, params):
        def __init__(*args, **kwargs):
            Repository.__init__(*args, **kwargs)
        repos = Mock(Repository, params['name'], params, self.log,
                     __init__=__init__)
        return CachedRepositoryStub(self.env, repos, self.log)


class CachedRepositoryStub(CachedRepository):

    def db_rev(self, rev):
        return '%05d' % int(rev)

    def rev_db(self, rev):
        return int(rev or 0)

    def get_youngest_rev(self):
        for row in self.env.db_query("""
                SELECT rev FROM revision WHERE repos=%s
                ORDER BY rev DESC LIMIT 1
                """, (self.id,)):
            return self.rev_db(row[0])

    def sync_changeset(self, rev):
        rev = self.db_rev(rev)
        for message, author, date in self.env.db_query("""
                SELECT message, author, time FROM revision
                WHERE repos=%s AND rev=%s
                """, (self.id, rev)):
            return Changeset(self, rev, message, author, from_utimestamp(date))

    def sync(self, *args, **kwargs):
        pass


class GatherLinksTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, path=_mkdtemp(),
                                   enable=['trac.*', RepositoryStubConnector])
        dir_ = pkg_resources.resource_filename('trac.wiki', 'default-pages')
        pages = pkg_resources.resource_listdir('trac.wiki', 'default-pages')
        with self.env.db_transaction:
            admin = WikiAdmin(self.env)
            for name in pages:
                filename = os.path.join(dir_, name)
                admin.import_page(filename, name)

    def tearDown(self):
        self.env.reset_db()

    def _gather(self, resource, text):
        return gather_links(self.env, resource, text)

    def test_ticket_links(self):
        with self.env.db_transaction:
            ticket = Ticket(self.env)
            ticket.populate({'type': 'defect', 'summary': 'test',
                             'reporter': 'anonymous', 'description': ''})
            tktid = ticket.insert()
        text = (u'** #42 // ticket:43 ** // #44\n'
                u'ticket:%(id)d\n'            # self-reference
                u'#%(id)d\n'                  # self-reference
                u'comment:1:ticket:%(id)d\n'  # self-reference
                u'Tést #52,54\n'
                u'Test ticket:53,55\n'
                u'[ticket:62 #63]\n'
                u'<ticket:72>\n'
                u'[[ticket:82|#83]]\n'
                u'comment:1\n'                # self-reference
                u'comment:21:ticket:92\n'
                u'[comment:22:ticket:93 Comment 22 in #93]\n'
                u'<comment:23:ticket:94>\n'
                u'[[comment:24:ticket:95|Comment 24 in #95]]\n'
                u'[=#anchor #102]\n'
                u'[=#anchor ticket:103]\n'
                u'[[=#anchor|#104,105]]\n'
                u'[[=#anchor|ticket:106]]\n'
                % {'id': tktid})
        actual = set(self._gather(ticket, text))
        expected = set()
        expected.update(Resource('ticket', id_)
                        for id_ in (42, 43, 44, 52, 53, 54, 55, 62, 72, 82,
                                    102, 103, 104, 105, 106))
        expected.add(Resource('ticket', 92).child('comment', 21))
        expected.add(Resource('ticket', 93).child('comment', 22))
        expected.add(Resource('ticket', 94).child('comment', 23))
        expected.add(Resource('ticket', 95).child('comment', 24))
        self.assertEqual(expected - (expected & actual),
                         actual - (expected & actual))

    def test_wiki_links(self):
        def test(expected, text):
            with self.env.db_transaction:
                page = WikiPage(self.env, 'SandBox/Sub/TracLicense')
                page.text = text
                _save_page(page, 'anonymous', None)
                page = WikiPage(self.env, 'SandBox/Sub/TracLinks')
                page.text = text
                _save_page(page, 'anonymous', None)
            actual = set(self._gather(page, page.text))
            expected = set(expected)
            self.assertEqual(expected - (expected & actual),
                             actual - (expected & actual))

        test([Resource('wiki', 'WikiStart')], 'wiki:WikiStart')
        test([], 'wiki:SandBox/Sub/TracLinks')  # self-reference

        resources = [Resource('wiki', 'TracUpgrade')]
        test(resources, 'TracUpgrade')
        test(resources, '/TracUpgrade/')
        test(resources, 'TracUpgrade@42')
        test(resources, 'TracUpgrade#anchor')
        test(resources, '/TracUpgrade@42#anchor')
        test(resources, '[TracUpgrade]')
        test(resources, '[TracUpgrade@42]')
        test(resources, '[TracUpgrade#anchor]')
        test(resources, '[TracUpgrade@42#anchor]')
        test(resources, '[TracUpgrade upgrade]')
        test(resources, '[TracUpgrade@42 upgrade]')
        test(resources, '[TracUpgrade#anchor upgrade]')
        test(resources, '[TracUpgrade@42#anchor upgrade]')
        test(resources, '[wiki:TracUpgrade upgrade]')
        test(resources, '[wiki:TracUpgrade@42 upgrade]')
        test(resources, '[wiki:TracUpgrade#anchor upgrade]')
        test(resources, '[wiki:/TracUpgrade@42#anchor upgrade]')

        resources = [Resource('wiki', 'SandBox/Sub/MissingPage')]
        test(resources, 'MissingPage')
        test(resources, 'MissingPage@42')
        test(resources, 'MissingPage#anchor')
        test(resources, 'MissingPage@42#anchor')
        test(resources, '[MissingPage]')
        test(resources, '[MissingPage@42]')
        test(resources, '[MissingPage#anchor]')
        test(resources, '[MissingPage@42#anchor]')
        test(resources, '[MissingPage missing page]')
        test(resources, '[MissingPage@42 missing page]')
        test(resources, '[MissingPage#anchor missing page]')
        test(resources, '[MissingPage@42#anchor missing page]')
        test(resources, 'wiki:MissingPage')
        test(resources, 'wiki:MissingPage@42')
        test(resources, 'wiki:MissingPage#anchor')
        test(resources, 'wiki:MissingPage@42#anchor')
        test(resources, '[wiki:MissingPage]')
        test(resources, '[wiki:MissingPage@42]')
        test(resources, '[wiki:MissingPage#anchor]')
        test(resources, '[wiki:MissingPage@42#anchor]')
        test(resources, '[wiki:MissingPage missing page]')
        test(resources, '[wiki:MissingPage@42 missing page]')
        test(resources, '[wiki:MissingPage#anchor missing page]')
        test(resources, '[wiki:MissingPage@42#anchor missing page]')

        resources = [Resource('wiki', 'TracInstall')]
        test(resources, '<TracInstall>')
        test(resources, '<TracInstall@42>')
        test(resources, '<TracInstall#anchor>')
        test(resources, '</TracInstall@42#anchor>')
        test(resources, '<wiki:TracInstall>')
        test(resources, '<wiki:TracInstall@42>')
        test(resources, '<wiki:TracInstall#anchor>')
        test(resources, '<wiki:/TracInstall@42#anchor>')

        resources = [Resource('wiki', 'TracGuide')]
        test(resources, '[[TracGuide]]')
        test(resources, '[[TracGuide@42]]')
        test(resources, '[[TracGuide#anchor]]')
        test(resources, '[[TracGuide@42#anchor]]')
        test(resources, '[[wiki:TracGuide]]')
        test(resources, '[[wiki:TracGuide@42]]')
        test(resources, '[[wiki:TracGuide#anchor]]')
        test(resources, '[[wiki:/TracGuide@42#anchor]]')
        test(resources, '[[wiki:TracGuide|Trac Guide]]')
        test(resources, '[[wiki:TracGuide@42|Trac Guide]]')
        test(resources, '[[wiki:TracGuide#anchor|Trac Guide]]')
        test(resources, '[[wiki:/TracGuide@42#anchor|Trac Guide]]')

        test([Resource('wiki', 'MissingPage')], 'wiki:/MissingPage')
        test([Resource('wiki', u'SandBox/Sub/föo')], u'wiki:föo')
        test([Resource('wiki', 'SandBox/Sub/bar')], '[wiki:bar Bar page]')
        test([Resource('wiki', 'SandBox/Sub/foo bar')], 'wiki:"foo bar"')
        test([Resource('wiki', 'SandBox/Sub/foo bar')],
             '[wiki:"foo bar" "Foo bar" page]')
        test([], '[/TracAdmin]')
        test([Resource('wiki', 'SandBox/Sub/TracLicense')],
             '[wiki:TracLicense]')
        test([], '[wiki:TracLinks]')
        test([Resource('wiki', 'TracLinks')], '[wiki:/TracLinks]')
        test([], '[wiki:.]')  # self-reference
        test([Resource('wiki', 'SandBox/Sub')], '[wiki:..]')
        test([Resource('wiki', 'SandBox')], '[wiki:../..]')

    def test_attachment_links(self):
        def test(expected, text):
            with self.env.db_transaction:
                page = WikiPage(self.env, 'SandBox')
                att = Attachment(self.env, page.realm, page.name)
                att.insert('test.txt', StringIO('test'), 4)
            actual = set(self._gather(page, text))
            expected = set(expected)
            self.assertEqual(expected - (expected & actual),
                             actual - (expected & actual))

        expected = [Resource('wiki', 'WikiStart').child('attachment',
                                                        'test.txt')]
        test([], 'attachment:test.txt')
        test(expected, 'attachment:test.txt:wiki:WikiStart')
        test(expected, 'raw-attachment:test.txt:wiki:WikiStart')
        test(expected, '[attachment:test.txt:wiki:WikiStart File]')
        test(expected, '[raw-attachment:test.txt:wiki:WikiStart File]')
        test(expected, '<attachment:test.txt:wiki:WikiStart>')
        test(expected, '<raw-attachment:test.txt:wiki:WikiStart>')
        test(expected, '[[attachment:test.txt:wiki:WikiStart|File]]')
        test(expected, '[[raw-attachment:test.txt:wiki:WikiStart|File]]')
        test([], 'attachment:test.txt:wiki:SandBox')  # self-reference
        test(expected, '[[Image(WikiStart:test.txt)]]')
        test([], '[[Image(test.txt)]]')
        test([], '[[Image(SandBox:test.txt)]]')
        test([], '[[Image(wiki:SandBox:test.txt)]]')

        expected = [Resource('ticket', 42).child('attachment', 'test.txt')]
        test(expected, '[[Image(#42:test.txt)]]')
        test(expected, '[[Image(ticket:42:test.txt)]]')


    def test_milestone_links(self):
        def test(expected, description):
            with self.env.db_transaction:
                milestone = Milestone(self.env, 'milestone3')
                milestone.description = description
                milestone.update()
            actual = set(self._gather(milestone, description))
            expected = set(expected)
            self.assertEqual(expected - (expected & actual),
                             actual - (expected & actual))

        test(set([Resource('milestone', 'milestone1'),
                  Resource('milestone', 'milestone2'),
                  Resource('milestone', 'milestone4'),
                  Resource('milestone', u'milé stoné')]),
             (u'milestone:milestone1\n'
              u'[milestone:milestone2 Milestone 2]\n'
              u'<milestone:milestone3>\n'  # self-reference
              u'[[milestone:milestone4|Milestone 4]]\n'
              u'milestone:"milé stoné"\n'))

    def test_changeset_links(self):
        repos_prov = DbRepositoryProvider(self.env)
        repos_prov.add_repository('', '/', 'stub')
        repos_prov.add_repository('foo', '/foo', 'stub')
        repos_prov.add_repository('bar', '/bar', 'stub')
        _add_cset(self.env, '', None, '00042')
        _add_cset(self.env, 'foo', None, '00043')
        _add_cset(self.env, 'bar', None, '00044')

        def test(expected, reponame, rev, message):
            repos = RepositoryManager(self.env).get_repository(reponame)
            cset = Changeset(repos, '00001', message, 'anonymous',
                             datetime.now(utc))
            actual = set(self._gather(cset, message))
            expected = set(expected)
            self.assertEqual(expected - (expected & actual),
                             actual - (expected & actual))

        test([Resource('repository', '').child('changeset', '00042')],
             '', '00042', 'changeset:42')
        test([Resource('repository', '').child('changeset', '00042')],
             '', '00042', '[42]')
        test([Resource('repository', '').child('changeset', '00042')],
             '', '00042', 'r42')
        test([Resource('repository', 'foo').child('changeset', '00043')],
             'foo', '00043', 'changeset:43/foo')
        test([Resource('repository', 'foo').child('changeset', '00043')],
             'foo', '00043', '[43/foo]')
        test([Resource('repository', 'foo').child('changeset', '00043')],
             'foo', '00043', 'r43/foo')

    def test_wiki_syntax(self):
        def test(expected, text):
            resource = Resource('wiki', '42')
            actual = set(self._gather(resource, text))
            expected = set(expected)
            self.assertEqual(expected - (expected & actual),
                             actual - (expected & actual))

        expected = [Resource('ticket', 42)]
        test(expected, '**#42**')
        test(expected, "'''#42'''")
        test(expected, "''#42''")
        test(expected, "'''''#42'''''")
        test(expected, '//#42//')
        test([], '//!#42//')
        test([], '{{{#42}}}')
        test([], '`#42`')
        test(expected, '= #42')
        test(expected, '===== ticket:42 #anchor')
        test(expected, '[=#anchor #42]')
        test(expected, ' * #42')
        test(expected, ' - #42')
        test(expected, ' 1. #42')
        test(expected, ' a. #42')
        test(expected, ' term :: #42')
        test(expected, ' #42 :: definition')
        test(expected, '  #42\n  #42\n')
        test(expected, '> #42\n')
        test(expected, '> > #42\n> ...\n')
        test(expected, '|| #42 ||')
        test(expected, '||= #42 =||')
        test(expected, '[[Span(#42)]]')
        test(expected, '[[span(#42)]]')
        test(expected, '{{{#!div\n'
                       '#42\n'
                       '}}}\n')
        test(expected, '{{{#!th\n'
                       '#42\n'
                       '}}}\n')
        test([], '{{{#!comment\n'
                 '#42\n'
                 '}}}\n')


class ChangeListenersTestCase(unittest.TestCase):

    _form_token = 'a' * 40

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, path=_mkdtemp(),
                                   enable=['trac.*', TracBackLinkSystem,
                                           RepositoryStubConnector])
        dir_ = pkg_resources.resource_filename('trac.wiki', 'default-pages')
        pages = pkg_resources.resource_listdir('trac.wiki', 'default-pages')
        with self.env.db_transaction:
            admin = WikiAdmin(self.env)
            for name in pages:
                filename = os.path.join(dir_, name)
                admin.import_page(filename, name)
        system = TracBackLinkSystem(self.env)
        system.environment_created()
        system._invoke = self._invoke

    def tearDown(self):
        DatabaseManager(self.env).drop_tables(db_default.schema)
        self.env.reset_db()

    def _invoke(self, name, f, *args, **kwargs):
        return f(*args, **kwargs)

    def _request(self, **kwargs):
        kwargs.setdefault('method', 'POST')
        kwargs.setdefault('form_token', self._form_token)
        return MockRequest(self.env, **kwargs)

    def _db_query(self, **kwargs):
        query = """\
            SELECT ref_realm, ref_id, ref_parent_realm, ref_parent_id,
                   src_realm, src_id, src_parent_realm, src_parent_id
            FROM backlink"""
        with self.env.db_query as db:
            where = []
            args = []
            for name, value in kwargs:
                where.append(db.quote(name) + '=%s')
                args.append(value)
            if where:
                query += ' WHERE ' + ' AND '.join(where)
            return db(query, args)

    def _verify_sets(self, s1, s2):
        s1 = set(s1)
        s2 = set(s2)
        self.assertEqual(s1 - (s1 & s2), s2 - (s1 & s2))

    def test_attachment(self):
        with self.env.db_transaction:
            page = WikiPage(self.env, 'SandBox')
            page.text = '.'
            _save_page(page, 'anonymous', '')
            t1 = Ticket(self.env)
            t1.populate({'summary': 'test attachment', 'status': 'new'})
            t1.insert()  # ticket:1
            self.assertEqual(1, t1.id)

        att = Attachment(self.env, page.realm, page.name)
        att.description = 'See #1, SandBox and TracIni'
        att.insert('foo.txt', StringIO('test'), 4)
        self._verify_sets([('wiki', 'TracIni', None, None,
                            'attachment', 'foo.txt', 'wiki', 'SandBox'),
                           ('ticket', '1', None, None,
                            'attachment', 'foo.txt', 'wiki', 'SandBox'),
                          ], self._db_query())

        att = Attachment(self.env, page.realm, page.name)
        att.description = 'See [milestone:milestone3]'
        att.insert('bar.txt', StringIO('test'), 4)
        self._verify_sets([('wiki', 'TracIni', None, None,
                            'attachment', 'foo.txt', 'wiki', 'SandBox'),
                           ('ticket', '1', None, None,
                            'attachment', 'foo.txt', 'wiki', 'SandBox'),
                           ('milestone', 'milestone3', None, None,
                            'attachment', 'bar.txt', 'wiki', 'SandBox'),
                          ], self._db_query())

        att = Attachment(self.env, 'ticket', t1.id)
        att.description = 'See WikiStart'
        att.insert('screen1.png', StringIO('test'), 4)
        att = Attachment(self.env, 'ticket', t1.id)
        att.description = 'See TracIni'
        att.insert('screen2.png', StringIO('test'), 4)
        self._verify_sets([('wiki', 'TracIni', None, None,
                            'attachment', 'foo.txt', 'wiki', 'SandBox'),
                           ('ticket', '1', None, None,
                            'attachment', 'foo.txt', 'wiki', 'SandBox'),
                           ('milestone', 'milestone3', None, None,
                            'attachment', 'bar.txt', 'wiki', 'SandBox'),
                           ('wiki', 'WikiStart', None, None,
                            'attachment', 'screen1.png', 'ticket', '1'),
                           ('wiki', 'TracIni', None, None,
                            'attachment', 'screen2.png', 'ticket', '1'),
                          ], self._db_query())

        page.rename('NewScreen')
        self._verify_sets([('wiki', 'TracIni', None, None,
                            'attachment', 'foo.txt', 'wiki', 'NewScreen'),
                           ('wiki', 'SandBox', None, None,
                            'attachment', 'foo.txt', 'wiki', 'NewScreen'),
                           ('ticket', '1', None, None,
                            'attachment', 'foo.txt', 'wiki', 'NewScreen'),
                           ('milestone', 'milestone3', None, None,
                            'attachment', 'bar.txt', 'wiki', 'NewScreen'),
                           ('wiki', 'WikiStart', None, None,
                            'attachment', 'screen1.png', 'ticket', '1'),
                           ('wiki', 'TracIni', None, None,
                            'attachment', 'screen2.png', 'ticket', '1'),
                          ], self._db_query())

        att = Attachment(self.env, page.realm, page.name, 'foo.txt')
        att.delete()
        self._verify_sets([('milestone', 'milestone3', None, None,
                            'attachment', 'bar.txt', 'wiki', 'NewScreen'),
                           ('wiki', 'WikiStart', None, None,
                            'attachment', 'screen1.png', 'ticket', '1'),
                           ('wiki', 'TracIni', None, None,
                            'attachment', 'screen2.png', 'ticket', '1'),
                          ], self._db_query())

        t1.delete()
        self._verify_sets([('milestone', 'milestone3', None, None,
                            'attachment', 'bar.txt', 'wiki', 'NewScreen'),
                          ], self._db_query())

        page.delete()
        self._verify_sets([], self._db_query())

    def test_wiki_page(self):
        page = WikiPage(self.env, 'SandBox/NewPage')
        page.text = 'See TracIni'
        _save_page(page, 'anonymous', 'Added hints (refs #42, comment:3:ticket:43)')
        self._verify_sets([('wiki', 'TracIni', None, None,
                            'wiki', 'SandBox/NewPage', None, None),
                           ('ticket', '42', None, None,
                            'comment', '1', 'wiki', 'SandBox/NewPage'),
                           ('comment', '3', 'ticket', '43',
                            'comment', '1', 'wiki', 'SandBox/NewPage'),
                          ], self._db_query())

        page = WikiPage(self.env, 'SandBox/NewPage')
        page.text = 'See TracInstall'
        _save_page(page, 'anonymous', 'Minor changes (#44)')
        expected = [('wiki', 'TracInstall', None, None,
                     'wiki', 'SandBox/NewPage', None, None),
                    ('ticket', '42', None, None,
                     'comment', '1', 'wiki', 'SandBox/NewPage'),
                    ('comment', '3', 'ticket', '43',
                     'comment', '1', 'wiki', 'SandBox/NewPage'),
                    ('ticket', '44', None, None,
                     'comment', '2', 'wiki', 'SandBox/NewPage'),
                   ]
        self._verify_sets(expected, self._db_query())

        WikiPage(self.env, 'TracInstall').delete()
        self._verify_sets(expected, self._db_query())

        WikiPage(self.env, 'SandBox/NewPage').delete(version=2)
        self._verify_sets([('wiki', 'TracIni', None, None,
                            'wiki', 'SandBox/NewPage', None, None),
                           ('ticket', '42', None, None,
                            'comment', '1', 'wiki', 'SandBox/NewPage'),
                           ('comment', '3', 'ticket', '43',
                            'comment', '1', 'wiki', 'SandBox/NewPage'),
                          ], self._db_query())

    def test_ticket(self):
        config = self.env.config
        config.set('ticket-custom', 'text_plain', 'text')
        config.set('ticket-custom', 'text_wiki', 'text')
        config.set('ticket-custom', 'text_wiki.format', 'wiki')
        config.set('ticket-custom', 'textarea_plain', 'textarea')
        config.set('ticket-custom', 'textarea_wiki', 'textarea')
        config.set('ticket-custom', 'textarea_wiki.format', 'wiki')
        tktsys = TicketSystem(self.env)
        del tktsys.fields

        t1 = Ticket(self.env)
        t1.populate({'summary': 'test 1', 'status': 'new'})
        t1.insert()  # ticket:1
        self.assertEqual([], self._db_query())
        t1.save_changes('anonymous', '...')

        t2 = Ticket(self.env)
        t2.populate({'summary': 'test 2', 'status': 'new',
                     'description': '#1'})
        t2.insert()  # ticket:2
        self._verify_sets([('ticket', '1', None, None,
                            'ticket', '2', None, None),
                          ], self._db_query())
        for i in xrange(5):
            t2.save_changes('anonymous', '...')

        t3 = Ticket(self.env)
        t3.populate({'summary': 'test 3', 'status': 'new',
                     'description': 'comment:1:ticket:2',
                     'text_plain': 'comment:2:ticket:2',
                     'text_wiki': 'comment:3:ticket:2',
                     'textarea_plain': 'comment:4:ticket:2',
                     'textarea_wiki': 'comment:5:ticket:2'})
        t3.insert()  # ticket:3
        self._verify_sets([('ticket', '1', None, None,
                            'ticket', '2', None, None),
                           ('comment', '1', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '3', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '5', 'ticket', '2',
                            'ticket', '3', None, None),
                          ], self._db_query())

        t3.save_changes('anonymous', 'See comment:1:ticket:2',
                        replyto='description')
        t3c1 = t3['changetime']
        self._verify_sets([('ticket', '1', None, None,
                            'ticket', '2', None, None),
                           ('comment', '1', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '3', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '5', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '1', 'ticket', '2',
                            'comment', '1', 'ticket', '3'),
                          ], self._db_query())

        t3.save_changes('anonymous', 'See comment:1:ticket:1', replyto='1')
        t3c2 = t3['changetime']
        self._verify_sets([('ticket', '1', None, None,
                            'ticket', '2', None, None),
                           ('comment', '1', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '3', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '5', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '1', 'ticket', '2',
                            'comment', '1', 'ticket', '3'),
                           ('comment', '1', 'ticket', '1',
                            'comment', '2', 'ticket', '3'),
                          ], self._db_query())

        t3.modify_comment(t3c2, 'admin', 'See comment:2:ticket:1 and TracIni')
        self._verify_sets([('ticket', '1', None, None,
                            'ticket', '2', None, None),
                           ('comment', '1', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '3', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '5', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '1', 'ticket', '2',
                            'comment', '1', 'ticket', '3'),
                           ('comment', '2', 'ticket', '1',
                            'comment', '2', 'ticket', '3'),
                           ('wiki', 'TracIni', None, None,
                            'comment', '2', 'ticket', '3'),
                          ], self._db_query())

        t3.delete_change(cdate=t3c1)
        self._verify_sets([('ticket', '1', None, None,
                            'ticket', '2', None, None),
                           ('comment', '1', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '3', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '5', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '2', 'ticket', '1',
                            'comment', '2', 'ticket', '3'),
                           ('wiki', 'TracIni', None, None,
                            'comment', '2', 'ticket', '3'),
                          ], self._db_query())

        t2.delete()
        self._verify_sets([('comment', '1', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '3', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '5', 'ticket', '2',
                            'ticket', '3', None, None),
                           ('comment', '2', 'ticket', '1',
                            'comment', '2', 'ticket', '3'),
                           ('wiki', 'TracIni', None, None,
                            'comment', '2', 'ticket', '3'),
                          ], self._db_query())

    def test_milestone(self):
        milestone = Milestone(self.env)
        milestone.name = 'milestone5'
        milestone.description = 'wiki:WikiStart'
        milestone.insert()
        self._verify_sets([('wiki', 'WikiStart', None, None,
                            'milestone', 'milestone5', None, None),
                          ], self._db_query())

        milestone = Milestone(self.env, 'milestone4')
        milestone.description = '#42'
        milestone.update()
        self._verify_sets([('wiki', 'WikiStart', None, None,
                            'milestone', 'milestone5', None, None),
                           ('ticket', '42', None, None,
                            'milestone', 'milestone4', None, None),
                          ], self._db_query())

        Milestone(self.env, 'milestone5').delete()
        self._verify_sets([('ticket', '42', None, None,
                            'milestone', 'milestone4', None, None),
                          ], self._db_query())

    def test_changeset(self):
        rm = RepositoryManager(self.env)
        repos_prov = DbRepositoryProvider(self.env)
        repos_prov.add_repository('stub', '/stub', 'stub')
        repos = rm.get_repository('stub')
        _add_cset(self.env, 'stub', 'closes #123', '00042')
        _add_cset(self.env, 'stub', 'refs #124, comment:3:ticket:125', '00043')
        _add_cset(self.env, 'stub', '#126 #127', '00044')

        rm.notify('changeset_added', 'stub', ['42', '43'])
        self._verify_sets([('ticket', '123', None, None,
                            'changeset', '00042', 'repository', 'stub'),
                           ('ticket', '124', None, None,
                            'changeset', '00043', 'repository', 'stub'),
                           ('comment', '3', 'ticket', '125',
                            'changeset', '00043', 'repository', 'stub'),
                          ], self._db_query())

        rm.notify('changeset_added', 'stub', ['44'])
        self._verify_sets([('ticket', '123', None, None,
                            'changeset', '00042', 'repository', 'stub'),
                           ('ticket', '124', None, None,
                            'changeset', '00043', 'repository', 'stub'),
                           ('comment', '3', 'ticket', '125',
                            'changeset', '00043', 'repository', 'stub'),
                           ('ticket', '126', None, None,
                            'changeset', '00044', 'repository', 'stub'),
                           ('ticket', '127', None, None,
                            'changeset', '00044', 'repository', 'stub'),
                          ], self._db_query())

        self.env.db_transaction("""
            UPDATE revision SET message=%s WHERE repos=%s AND rev=%s
            """, ('refs #224', repos.id, '00043'))
        rm.notify('changeset_modified', 'stub', ['43'])
        self._verify_sets([('ticket', '123', None, None,
                            'changeset', '00042', 'repository', 'stub'),
                           ('ticket', '224', None, None,
                            'changeset', '00043', 'repository', 'stub'),
                           ('ticket', '126', None, None,
                            'changeset', '00044', 'repository', 'stub'),
                           ('ticket', '127', None, None,
                            'changeset', '00044', 'repository', 'stub'),
                          ], self._db_query())


def _add_cset(env, reponame, message, *revs):
    repos = RepositoryManager(env).get_repository(reponame)
    ts = to_utimestamp(datetime(2017, 1, 2, 12, 34, 56, 987654, utc))
    with env.db_transaction as db:
        db.executemany("""
            INSERT INTO revision (repos, rev, message, author, time)
            VALUES (%s,%s,%s,%s,%s)
            """, [(repos.id, rev, message, 'anonymous', ts) for rev in revs])


def _mkdtemp():
    return os.path.realpath(tempfile.mkdtemp(prefix='trac-testdir-'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GatherLinksTestCase))
    suite.addTest(unittest.makeSuite(ChangeListenersTestCase))
    return suite
