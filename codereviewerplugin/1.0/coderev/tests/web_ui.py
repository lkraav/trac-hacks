# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub, Mock, MockPerm, locale_en
from trac.util.datefmt import utc
from trac.web.api import RequestDone, _RequestArgs

from coderev.api import CodeReviewerSystem
from coderev.web_ui import CodeReviewerModule


def _revert_schema_init(env):
    with env.db_transaction as db:
        db("DROP TABLE IF EXISTS codereviewer")
        db("DROP TABLE IF EXISTS codereviewer_map")
        db("DELETE FROM system WHERE name='coderev'")


class CodeReviewerModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        CodeReviewerSystem(self.env).upgrade_environment()
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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CodeReviewerModuleTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
