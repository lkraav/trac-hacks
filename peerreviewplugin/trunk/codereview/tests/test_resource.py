# -*- coding: utf-8 -*-
# Copyright (c) 2019 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest
from codereview.model import PeerReviewModelProvider, ReviewFileModel
from codereview.peerReviewMain import PeerReviewMain
from datetime import datetime
from trac.resource import Resource, ResourceNotFound
from trac.test import EnvironmentStub
from trac.util.datefmt import to_datetime, to_utimestamp
from trac.web.href import Href


def _prepare_review_data(env):
    # owner, status, created, name, notes, parent_id
    revs = [
        ['Rev1', 'bar', to_utimestamp(to_datetime(datetime(2019, 2, 4))), 'name1', 'note1', 0],
        ['Rev1', 'closed', to_utimestamp(to_datetime(datetime(2019, 3, 4))), 'name2', 'note2', 0],
        ['Rev2', 'bar', to_utimestamp(to_datetime(datetime(2019, 3, 14))), 'name3', 'note3', 1],
        ['Rev3', 'foo', to_utimestamp(to_datetime(datetime(2019, 4, 4))), 'name4', 'note4', 2]
    ]

    with env.db_transaction as db:
        cursor = db.cursor()
        for rev in revs:
            cursor.execute("INSERT INTO peerreview (owner, status, created, name, notes, parent_id) "
                           "VALUES (%s,%s,%s,%s,%s,%s)", rev)


def _prepare_file_data(env):
    # review_id, path, start, end, revision, status
    files = [
        [1, '/foo/bar', 5, 100, '1234', 'new', None, 'repo1'],
        [1, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        [2, '/foo/bar', 5, 100, '1234', 'closed', None, 'repo1'],
        [2, '/foo/bar2', 6, 101, '12346', 'closed', None, 'repo1'],
        [2, '/foo/bar3', 7, 102, '12347', 'closed', None, 'repo1'],
        [3, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        [4, '/foo/bar', 5, 100, '1234', 'new', None, 'repo1'],
        [4, '/foo/bar2', 6, 101, '1234', 'new', None, 'repo1'],
        # File list data for several projects
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar2', 6, 101, '12346', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar3', 7, 102, '12347', 'new', 'PrjFoo', 'repo1'],
        [0, '/foo/bar/baz', 6, 101, '1234', 'new', 'PrjBar', 'repo1'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBaz', 'repo1'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjBaz', 'repo1'],
    ]
    for f in files:
        rfm = ReviewFileModel(env)
        rfm['review_id'] = f[0]
        rfm['path'] = f[1]
        rfm['line_start'] = f[2]
        rfm['line_end'] = f[3]
        rfm['revision'] = f[4]
        rfm['status'] = f[5]
        rfm['project'] = f[6]
        rfm['repo'] = f[7]
        rfm.insert()


class TestResource(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'codereview.model.*',
                                                             'codereview.peerreviewnew.*',
                                                             'codereview.peerreviewmain.*',
                                                             'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.plugin = PeerReviewMain(self.env)
        _prepare_review_data(self.env)
        _prepare_file_data(self.env)

    def tearDown(self):
        self.env.shutdown()

    def test_get_resourece_realms(self):
        realms = list(self.plugin.get_resource_realms())
        realms = list(set(realms))
        self.assertEqual(2, len(realms))
        for item in realms:
            self.assertIn(item, ('peerreview', 'peerreviewfile'))

    def test_get_resource_description(self):
        resource = Resource('peerreview', 1)
        self.assertEqual('Review 1', self.plugin.get_resource_description(resource))
        self.assertEqual('review:1', self.plugin.get_resource_description(resource, 'compact'))
        resource = Resource('peerreviewfile', 1)
        self.assertEqual('ReviewFile 1', self.plugin.get_resource_description(resource))
        self.assertEqual('rfile:1', self.plugin.get_resource_description(resource, 'compact'))

    def test_get_resource_description_wrong_resource(self):
        resource = Resource('wiki', 'WikiStart')
        self.assertEqual('', self.plugin.get_resource_description(resource))

    def test_resource(self):
        resource = Resource('peerreview', 1)
        self.assertEqual("<Resource 'peerreview:1'>", str(resource).replace("u'", "'"))
        res = Resource('peerreview', 1)
        resource = Resource(res, 2)  # This creates a copy
        self.assertEqual("<Resource 'peerreview:2'>", str(resource).replace("u'", "'"))

        resource = Resource('peerreviewfile', 1)
        self.assertEqual("<Resource 'peerreviewfile:1'>", str(resource).replace("u'", "'"))
        res = Resource('peerreviewfile', 1)
        resource = Resource(res, 2)  # This creates a copy
        self.assertEqual("<Resource 'peerreviewfile:2'>", str(resource).replace("u'", "'"))

    def test_resource_exists_peerreview(self):
        for num in range(1, 5):
            resource = Resource('peerreview', num)
            self.assertTrue(self.plugin.resource_exists(resource))
        # Invalid review id
        resource = Resource('peerreview', 12)
        self.assertFalse(self.plugin.resource_exists(resource))

    def test_resource_exists_peerreviewfile(self):
        for num in range(1, 9):
            resource = Resource('peerreviewfile', num)
            self.assertTrue(self.plugin.resource_exists(resource))
        # Only files associated with a review are real peerreviewfiles
        for num in range(9, 17):
            resource = Resource('peerreviewfile', num)
            self.assertFalse(self.plugin.resource_exists(resource))
        # Invalid file id
        resource = Resource('peerreviewfile', 22)
        self.assertFalse(self.plugin.resource_exists(resource))

    def test_resource_exist_wrong_resource(self):
        resource = Resource('wiki', 'WikiStart')
        self.assertRaises(ResourceNotFound, self.plugin.resource_exists, resource)

    def test_get_resource_url(self):
        href = Href('foo')
        resource = Resource('peerreview', 1)
        self.assertEqual('foo/peerreviewview/1' , self.plugin.get_resource_url(resource, href))

        resource = Resource('peerreviewfile', 1)
        self.assertEqual('foo/peerreviewfile/1' , self.plugin.get_resource_url(resource, href))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestResource))
    return suite
