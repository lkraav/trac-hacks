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

from trac.db.api import DatabaseManager
from trac.perm import PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub

from tracdiscussion.api import DiscussionApi
from tracdiscussion.init import DiscussionInit


class DiscussionBaseTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.realm = 'discussion'

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
                   (name, subject, description)
            VALUES (%s,%s,%s)
        """, [('forum1', 'forum-subject1', 'forum-desc1'),
              ('forum2', 'forum-subject2', 'forum-desc2')
             ])
        cursor.executemany("""
            INSERT INTO topic
                   (forum, subject, body)
            VALUES (%s,%s,%s)
        """, [(1, 'top1', 'topic-desc1'),
              (1, 'top2', 'Othello ;-)'),
              (2, 'top3', 'topic-desc3')
             ])
        cursor.executemany("""
            INSERT INTO message
                   (forum, topic, body, replyto, time)
            VALUES (%s,%s,%s,%s,%s)
        """, [(1, 1, 'msg1', -1, 1400361000),
              (1, 2, 'Say "Hello world!"', -1, 1400362000),
              (1, 2, 'msg3', 2, 1400362200),
              (1, 2, 'msg4', -1, 1400362400),
              (2, 3, 'msg5', -1, 1400362600)
             ])

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)
