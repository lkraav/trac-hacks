# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import io
import sys
import unittest

from trac.admin.api import AdminCommandManager
from trac.db.api import DatabaseManager
from trac.test import EnvironmentStub
from trac.ticket.model import Ticket

from .. import db_default
from ..admin import TracBackLinkCommandProvider
from ..api import TracBackLinkSystem
from .api import _import_default_pages, _mkdtemp


class AdminCommandTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, path=_mkdtemp(),
                                   enable=['trac.*'])
        for cls in (TracBackLinkSystem, TracBackLinkCommandProvider):
            self.env.enable_component(cls)
        TracBackLinkSystem(self.env).environment_created()
        _import_default_pages(self.env)
        with self.env.db_transaction:
            ids = [
                self._create_ticket('backlink', description='wiki:WikiStart'),
                self._create_ticket('backlink', description='wiki:SandBox'),
            ]
            self._create_ticket('backlink',
                                description='#{}, ticket:{}'.format(*ids))

    def tearDown(self):
        DatabaseManager(self.env).drop_tables(db_default.schema)
        self.env.reset_db_and_disk()

    def _create_ticket(self, summary, **kwargs):
        tkt = Ticket(self.env)
        tkt['summary'] = summary
        for col in kwargs:
            tkt[col] = kwargs[col]
        return tkt.insert()

    def _backlinks_count(self):
        query = 'SELECT src_realm, COUNT(*) FROM backlink GROUP BY src_realm'
        counts = {row[0]: row[1] for row in self.env.db_query(query)}
        for realm in ('wiki', 'ticket', 'milestone', 'changeset'):
            counts.setdefault(realm, 0)
        return counts

    def _execute(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        saved = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr
        try:
            rc = AdminCommandManager(self.env).execute_command(*args)
        finally:
            sys.stdout, sys.stderr = saved
        return rc, stdout.getvalue(), stderr.getvalue()

    def test_sync(self):
        self.env.db_transaction('DELETE FROM backlink')

        self._execute('backlink', 'sync')
        counts = self._backlinks_count()
        self.assertNotEqual(0, counts['wiki'])
        self.assertEqual(4, counts['ticket'])

        self.env.db_transaction("UPDATE ticket SET description=''")
        self._execute('backlink', 'sync', 'ticket', '3')
        counts = self._backlinks_count()
        self.assertEqual(2, counts['ticket'])

        self._execute('backlink', 'sync', 'ticket')
        counts = self._backlinks_count()
        self.assertEqual(0, counts['ticket'])


def test_suite():
    suite = unittest.TestSuite()
    load = unittest.defaultTestLoader.loadTestsFromTestCase
    for testcase in [AdminCommandTestCase]:
        suite.addTest(load(testcase))
    return suite
