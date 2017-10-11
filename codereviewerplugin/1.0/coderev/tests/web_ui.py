# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from datetime import datetime
import unittest

from trac.test import EnvironmentStub, Mock, MockPerm, locale_en
from trac.util.datefmt import to_utimestamp, utc
from trac.web.api import RequestDone, _RequestArgs
from trac.versioncontrol.api import Changeset, Repository

from coderev.api import CodeReviewerSystem
from coderev.web_ui import ChangesetTicketMapper, CodeReviewerModule


def _upgrade_environment(env):
    CodeReviewerSystem(env).upgrade_environment()


def _revert_schema_init(env):
    with env.db_transaction as db:
        db("DROP TABLE IF EXISTS codereviewer")
        db("DROP TABLE IF EXISTS codereviewer_map")
        db("DELETE FROM system WHERE name='coderev'")


class CodeReviewerModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        _upgrade_environment(self.env)
        self.url = None

    def tearDown(self):
        _revert_schema_init(self.env)
        self.env.reset_db()

    def _create_request(self, authname='anonymous', **kwargs):
        kw = {'path_info': '/', 'perm': MockPerm(), 'args': {},
              'href': self.env.href, 'abs_href': self.env.abs_href,
              'tz': utc, 'locale': None, 'lc_time': locale_en,
              'session': {}, 'authname': authname,
              'chrome': {'notices': [], 'warnings': []},
              'method': None, 'get_header': lambda v: None, 'is_xhr': False,
              'form_token': None, }
        kw.update(kwargs)
        def redirect(url, permanent=False):
            self.url = url
            raise RequestDone
        return Mock(add_redirect_listener=lambda x: [].append(x),
                    redirect=redirect, **kw)

    def test_save_status(self):
        repos = Mock(reponame='repos1', short_rev=lambda c: int(c),
                     db_rev=lambda rev: '%010d' % rev)
        changeset = Mock(rev=1, repos=repos)
        args = _RequestArgs(tickets=None, status='PASSED',
                            summary='the summary')
        req = self._create_request(method='POST', path_info='/changeset/1',
                                   args=args)
        crm = CodeReviewerModule(self.env)
        data = {'changeset': changeset}

        self.assertRaises(RequestDone, crm.post_process_request, req,
                          None, data, None)
        self.assertEqual('/trac.cgi/changeset/1', self.url)


class ChangesetTicketMapperTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        _upgrade_environment(self.env)
        self.mapper = ChangesetTicketMapper(self.env)

    def tearDown(self):
        _revert_schema_init(self.env)
        self.env.reset_db()

    def _make_repos(self, name, id=1):
        params = {'name': name, 'id': id}
        return Mock(Repository, name, params, self.env.log)

    def _make_changeset(self, repos, rev, message, author='anonymous',
                        date=None):
        return Mock(Changeset, repos, rev, message, author,
                    date or datetime.now(utc))

    def _fetch_map_records(self, changeset):
        return self.env.db_query("""
            SELECT ticket,time FROM codereviewer_map
            WHERE repo=%s AND changeset=%s
            """, (changeset.repos.name, str(changeset.rev)))

    def test_changeset_events(self):
        repos = self._make_repos('')
        when = datetime(2017, 9, 21, 12, 34, 56, 987654, utc)
        when_ts = to_utimestamp(when)

        cset = self._make_changeset(
            repos, 42, 'refs #4242, #4241, #1\ncloses #2424, #4241, #2\n',
            'anonymous', when)
        self.mapper.changeset_added(repos, cset)
        rows = self._fetch_map_records(cset)
        self.assertEqual(['1', '2', '2424', '4241', '4242'],
                         sorted(row[0] for row in rows))
        self.assertEqual([when_ts], list(set(row[1] for row in rows)))

        self.mapper.changeset_added(repos, cset)
        self.assertEqual(rows, self._fetch_map_records(cset))

        cset = self._make_changeset(
            repos, 42, 'refs #4242, #4241, #1\ncloses #2424, #4241, #2\n',
            'anonymous', when)
        self.mapper.changeset_added(repos, cset)

        new_cset = self._make_changeset(repos, 42, 'refs #987', 'anonymous', when)
        self.mapper.changeset_modified(repos, new_cset, cset)
        rows = self._fetch_map_records(new_cset)
        self.assertEqual(['987'], sorted(row[0] for row in rows))
        self.assertEqual([when_ts], sorted(row[1] for row in rows))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeReviewerModuleTestCase))
    suite.addTest(unittest.makeSuite(ChangesetTicketMapperTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
