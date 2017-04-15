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

from trac.perm import PermissionCache, PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, MockRequest

from tracdiscussion.init import DiscussionInit
from tracdiscussion.tags import DiscussionTagProvider

from tractags.db import TagSetup


class DiscussionTagProviderTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*',
                                           'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        # Accomplish Discussion db schema setup.
        setup = DiscussionInit(self.env)
        setup.upgrade_environment()

        # Populate tables with initial test data.
        with self.env.db_transaction as db:
            cursor = db.cursor()
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

        tag_setup = TagSetup(self.env)
        # Current tractags schema is setup with enabled component anyway.
        #   Revert these changes for getting default permissions inserted.
        self._revert_tractags_schema_init()
        tag_setup.upgrade_environment()

        self.anon_req = MockRequest(self.env)
        self.anon_req.perm = PermissionCache(self.env)

        user = 'editor'
        self.req = MockRequest(self.env, authname=user)
        self.req.authname = user
        self.perms.grant_permission(user, 'DISCUSSION_VIEW')
        self.req.perm = PermissionCache(self.env, username=user)

        self.realm = 'discussion'
        self.forum = Resource(self.realm, 'forum/1')
        self.topic = Resource(self.realm, 'topic/2')
        self.message = Resource(self.realm, 'message/3', None, self.topic)

        self.dtp = DiscussionTagProvider(self.env)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _revert_tractags_schema_init(self):
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("DROP TABLE IF EXISTS tags")
            cursor.execute("DROP TABLE IF EXISTS tags_change")
            cursor.execute("DELETE FROM system WHERE name='tags_version'")
            cursor.execute("DELETE FROM permission WHERE action %s"
                           % db.like(), ('TAGS_%',))

    # Tests

    def test_describe_tagged_resource(self):
        desc = self.dtp.describe_tagged_resource  # method shorthand
        req = self.req
        self.assertEqual(desc(req, self.forum), '#1')
        self.assertEqual(desc(req, self.topic), '#2')
        self.assertEqual(desc(req, self.message), '#3')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionTagProviderTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
