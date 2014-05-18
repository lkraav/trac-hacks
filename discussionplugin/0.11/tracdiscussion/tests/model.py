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

from datetime import timedelta

from trac.mimeview import Context
from trac.perm import PermissionCache, PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock
from trac.util.datefmt import to_datetime, utc

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
            INSERT INTO forum_group
                   (name, description)
            VALUES (%s,%s)
        """, ('forum_group1', 'group-desc'))
        cursor.executemany("""
            INSERT INTO forum
                   (forum_group, name, subject, description)
            VALUES (%s,%s,%s,%s)
        """, [(0, 'forum1', 'forum-subject1', 'forum-desc1'),
              (1, 'forum2', 'forum-subject2', 'forum-desc2'),
              (1, 'forum3', 'forum-subject3', 'forum-desc3'),
             ])
        cursor.executemany("""
            INSERT INTO topic
                   (forum, subject, body)
            VALUES (%s,%s,%s)
        """, [(1, 'top1', 'topic-desc1'),
              (1, 'top2', 'topic-desc2'),
             ])
        cursor.executemany("""
            INSERT INTO message
                   (forum, topic, body, replyto)
            VALUES (%s,%s,%s,%s)
        """, [(1, 1, 'msg1', -1),
              (1, 2, 'msg2', -1),
              (1, 2, 'msg3', 2),
              (1, 2, 'msg4', 3),
             ])

        self.realm = 'discussion'
        self.ddb = DiscussionDb(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _prepare_context(self, req):
        context = Context.from_request(req)
        context.db = self.db
        return context        

    # Tests

    def test_get_item(self):
        context = self._prepare_context(self.req)
        self.assertEqual(self.ddb._get_item(context, 'topic', ('id',)),
                         dict(id=1))

    def test_get_items(self):
        context = self._prepare_context(self.req)
        cols = ('forum', 'subject')
        # Empty result list case.
        self.assertEqual(self.ddb._get_items(context, 'topic', cols,
                                             'forum=%s', (3,)), [])
        # Ordered result list by subject (reversed).
        self.assertEqual(self.ddb._get_items(context, 'topic', cols,
                                             order_by=cols[1], desc=True),
                         [dict(forum=1, subject='top2'),
                          dict(forum=1, subject='top1')])

    def test_get_groups(self):
        context = self._prepare_context(self.req)
        # Order is known because of list concatenation in this method.
        self.assertEqual(self.ddb.get_groups(context),
                         [dict(id=0, forums=1, name='None',
                               description='No Group'),
                          dict(id=1, forums=2, name='forum_group1',
                               description='group-desc')])

    def test_get_changed_topics(self):
        context = self._prepare_context(self.req)
        start = to_datetime(None, tzinfo=utc)
        stop = start - timedelta(seconds=1)
        self.assertEqual(
            list(self.ddb.get_changed_topics(context, start, stop)), [])

    def test_get_messages(self):
        context = self._prepare_context(self.req)
        self.assertEqual(
            self.ddb.get_messages(context, 2), [{
            'author': None, 'body': u'msg2', 'replyto': -1, 'time': None,
            'replies': [{'author': None, 'body': u'msg3', 'replyto': 2,
                         'time': None,
                         'replies': [{'author': None, 'body': u'msg4',
                                      'replyto': 3, 'time': None, 'id': 4}],
                         'id': 3}],
            'id': 2}]
        )

    def test_get_changed_messages(self):
        context = self._prepare_context(self.req)
        start = to_datetime(None, tzinfo=utc)
        stop = start - timedelta(seconds=1)
        self.assertEqual(
            list(self.ddb.get_changed_messages(context, start, stop)), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionDbTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
