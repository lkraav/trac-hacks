# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.mimeview import Context
from trac.perm import PermissionCache, PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock

from tracdiscussion.init import DiscussionInit
from tracdiscussion.model import DiscussionDb


class DiscussionDbTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.req = Mock(authname='editor', method='GET',
                   args=dict(), abs_href=self.env.abs_href,
                   chrome=dict(notices=[], warnings=[]),
                   href=self.env.abs_href, locale='',
                   redirect=lambda x: None, session=dict(), tz=''
        )
        self.req.perm = PermissionCache(self.env, 'editor')

        self.actions = ('DISCUSSION_ADMIN', 'DISCUSSION_MODERATE',
                        'DISCUSSION_ATTACH', 'DISCUSSION_APPEND',
                        'DISCUSSION_VIEW')
        self.db = self.env.get_db_cnx()
        # Accomplish Discussion db schema setup.
        setup = DiscussionInit(self.env)
        setup.upgrade_environment(self.db)
        # Populate tables with initial test data.
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO forum
                   (name, subject, description)
            VALUES (%s,%s,%s)
        """, ('forum1', 'forum-subject', 'forum-desc1'))
        cursor.executemany("""
            INSERT INTO topic
                   (forum, subject, body)
            VALUES (%s,%s,%s)
        """, [(1, 'top1', 'topic-desc1'),
              (1, 'top2', 'topic-desc2'),
             ])
        cursor.executemany("""
            INSERT INTO message
                   (forum, topic, body)
            VALUES (%s,%s,%s)
        """, [(1, 1, 'msg1'),
              (1, 2, 'msg2'),
              (1, 2, 'msg3'),
              (1, 2, 'msg4'),
             ])

        self.realm = 'discussion'
        self.ddb = DiscussionDb(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_get_item(self):
        context = Context.from_request(self.req)
        context.db = self.db
        self.assertEqual(self.ddb._get_item(context, 'topic', ['id']),
                         dict(id=1))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionDbTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
