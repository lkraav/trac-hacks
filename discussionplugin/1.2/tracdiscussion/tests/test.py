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

from trac.perm import PermissionSystem
from trac.test import EnvironmentStub

from tracdiscussion.init import DiscussionInit


class DiscussionBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.realm = 'discussion'

        # Accomplish Discussion db schema setup.
        setup = DiscussionInit(self.env)
        setup.upgrade_environment()
        with self.env.db_transaction as db:
            insert_test_data(db)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)


def insert_test_data(db):
    """Populate tables with initial test data."""
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO forum_group
               (name, description)
        VALUES (%s,%s)
    """, ('forum_group1', 'group-desc'))
    cursor.executemany("""
        INSERT INTO forum
               (forum_group, name, subject, description, time)
        VALUES (%s,%s,%s,%s,%s)
    """, [(0, 'forum1', 'forum-subject1', 'forum-desc1', 1400361000),
          (1, 'forum2', 'forum-subject2', 'forum-desc2', 1400361100),
          ])
    cursor.executemany("""
        INSERT INTO topic
               (forum, subject, body, time)
        VALUES (%s,%s,%s,%s)
    """, [(1, 'top1', 'topic-desc1', 1400361200),
          (1, 'top2', 'Othello ;-)', 1400361300),
          (2, 'top3', 'topic-desc3', 1400361400)
          ])
    cursor.executemany("""
        INSERT INTO message
               (forum, topic, body, replyto, time)
        VALUES (%s,%s,%s,%s,%s)
    """, [(1, 1, 'msg1', -1, 1400361500),
          (1, 2, 'Say "Hello world!"', -1, 1400362000),
          (1, 2, 'msg3', 2, 1400362200),
          (1, 2, 'msg4', -1, 1400362400),
          (2, 3, 'msg5', -1, 1400362600)
          ])
