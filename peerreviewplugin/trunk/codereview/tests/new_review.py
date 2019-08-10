# -*- coding: utf-8 -*-
# Copyright (c) 2016-2019 Cinc
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
from codereview.model import get_users, ReviewFileModel, PeerReviewModel, PeerReviewerModel, PeerReviewModelProvider
from codereview.peerReviewNew import add_users_to_data, create_file_hash_id, NewReviewModule
from datetime import datetime
from trac.admin.console import TracAdmin
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.util.datefmt import to_datetime, to_utimestamp


def _add_permissions(env):
    admin = TracAdmin()
    admin.env_set('Testenv', env)
    admin.onecmd("permission add Tester TICKET_VIEW")  # User not allowed to perform code reviews
    admin.onecmd("permission add Rev1 TRAC_ADMIN")
    admin.onecmd("permission add Rev2 CODE_REVIEW_DEV")
    admin.onecmd("permission add Rev3 CODE_REVIEW_MGR")
    admin.onecmd("permission add Rev1 RevGroup")
    admin.onecmd("permission add Rev2 RevGroup")


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

# reviewer (name), review_id
names = (['user1', 3], ['user2', 3], ['user3', 3],
         ['user4', 4], ['user5', 4],
         ['user4', 2], ['user5', 2],
         ['user2', 1], ['user3', 1], ['user4', 1], ['user5', 1])

def _prepare_users_for_review(env):
    for user in names:
        rev = PeerReviewerModel(env)
        rev['review_id'] = user[1]
        rev['reviewer'] = user[0]
        rev['vote'] = -1
        rev.insert()


class TestCreateFileHashId(unittest.TestCase):

    def test_hash(self):

        f = {
            'path': "path",
            'revision': 123,
            'line_start': 1234,
            'line_end': 5678,
            'repo': 'Repo'
        }
        self. assertEqual('id1230698611', create_file_hash_id(f))


class TestNewReviewModule(unittest.TestCase):

    def _add_permissions(self, env):
        admin = TracAdmin()
        admin.env_set('Testenv', env)
        admin.onecmd("permission add Tester TICKET_VIEW")  # User not allowed to perform code reviews
        admin.onecmd("permission add Rev1 TRAC_ADMIN")  # This one is also an allowed user
        admin.onecmd("permission add Rev2 TICKET_VIEW")
        admin.onecmd("permission add Rev3 TICKET_VIEW")
        admin.onecmd("permission add Rev1 RevGroup")
        admin.onecmd("permission add Rev2 RevGroup")
        for item in set([usr[0] for usr in names]):
            admin.onecmd("permission add %s CODE_REVIEW_DEV" % item)

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'codereview.model.*',
                                                             'codereview.peerreviewnew.*',
                                                             'codereview.peerreviewmain.*',
                                                             'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.plugin = NewReviewModule(self.env)
        self.req = Mock(href=Mock(), perm=MockPerm(), args={}, authname="Tester")
        _prepare_review_data(self.env)
        _prepare_file_data(self.env)
        _prepare_users_for_review(self.env)
        self._add_permissions(self.env)

    def tearDown(self):
        self.env.shutdown()

    def test_get_active_navigation_item(self):
        self.assertEqual('peerReviewMain', self.plugin.get_active_navigation_item(self.req))

    def test_get_navigation_items(self):
        self.assertEqual(0, len(self.plugin.get_navigation_items(self.req)))

    def test_save_changes_no_file_check(self):
        """Test save_changes() method. Only User and review data changes are tested. File changes are ignored."""
        # args is empty so we have no id for getting a review. Tracgenericclass will complain
        # when trying to save a review during this method which is not in the database yet.
        self.assertRaises(AssertionError, self.plugin.save_changes, self.req)
        # Check data before calling the method
        rev_pre = PeerReviewModel(self.env, 1)
        self.assertEqual('note1', rev_pre['notes'])
        before_users = [item[0] for item in names if item[1] == 1]
        data = {}
        add_users_to_data(self.env, 1, data)
        self.assertItemsEqual(before_users, data['assigned_users'])
        for item in before_users:
            self.assertIn(item, data['assigned_users'])

        new_users = ['user3', 'user4', 'user1']
        self.req.args.update({'oldid': 1,
                              'Name': 'New name 1',
                              'Notes': 'New note',
                              'project': 'PrjBar',
                              'user': new_users})

        self.plugin.save_changes(self.req)
        # Check Review data
        rev = PeerReviewModel(self.env, 1)
        self.assertEqual('New note', rev['notes'])
        self.assertEqual('New name 1', rev['name'])
        self.assertEqual('PrjBar', rev['project'])
        # Check new assigned user list
        data = {}
        add_users_to_data(self.env, 1, data)
        self.assertItemsEqual(new_users, data['assigned_users'])
        for item in new_users:
            self.assertIn(item, data['assigned_users'])
        # Check if reviewers are correct. Note that two users were removed and a new one added
        reviewers = list(PeerReviewerModel.select_by_review_id(self.env, 1))
        self.assertEqual(3, len(reviewers))
        for rev in reviewers:
            self.assertIn(rev['reviewer'], new_users)

    def test_save_changes_file_check_only(self):
        """Test save_changes() method. Only file changes are tested."""
        # args is empty so we have no id for getting a review. Tracgenericclass will complain
        # when trying to save a review during this method which is not in the database yet.
        self.assertRaises(AssertionError, self.plugin.save_changes, self.req)
        # Check data before calling the method
        rev_pre = PeerReviewModel(self.env, 1)
        self.assertEqual('note1', rev_pre['notes'])
        before_files = list(ReviewFileModel.select_by_review(self.env, 1))
        self.assertEqual(2, len(before_files))
        before_users = [item[0] for item in names if item[1] == 1]
        new_users = before_users
        # Create the list of files for review 1
        new_files = []
        for f in before_files:
            new_files.append(u"%s,%s,%s,%s,%s" % (f['path'], f['revision'], f['line_start'], f['line_end'], f['repo']))
        self.req.args.update({'oldid': 1,
                              'Name': 'New name 1',
                              'Notes': 'New note',
                              'project': 'PrjBar',
                              'user': new_users,
                              'file': new_files})

        # Test starts here
        self.plugin.save_changes(self.req)
        # Simple check of new assigned user list
        data = {}
        add_users_to_data(self.env, 1, data)
        self.assertItemsEqual(before_users, data['assigned_users'])
        for item in new_users:
            self.assertIn(item, data['assigned_users'])
        # Now check files. Note that you only can remove files not add them
        after_files = list(ReviewFileModel.select_by_review(self.env, 1))
        self.assertEqual(2, len(after_files))
        file_list = [item['path'] for item in before_files]
        for file_ in after_files:
            self.assertIn(file_['path'], file_list)

        # Now remove one of the files
        new_files = []
        for f in before_files[1:]:
            new_files.append(u"%s,%s,%s,%s,%s" % (f['path'], f['revision'], f['line_start'], f['line_end'], f['repo']))
        self.req.args['file'] = new_files
        self.assertEqual(1, len(self.req.args['file']))
        # Test starts here
        self.plugin.save_changes(self.req)
        after_files = list(ReviewFileModel.select_by_review(self.env, 1))
        self.assertEqual(1, len(after_files))


class TestUserHandling(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*',
                                          'codereview.model.*',
                                          'codereview.peerreviewnew.*',
                                          'codereview.peerreviewmain.*',
                                          'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(self.env).environment_created()
        self.plugin = NewReviewModule(self.env)
        _add_permissions(self.env)
        reviewer = PeerReviewerModel(self.env)
        reviewer['review_id'] = 1
        reviewer['reviewer'] = 'Rev1'
        reviewer.insert()
        reviewer = PeerReviewerModel(self.env)
        reviewer['review_id'] = 1
        reviewer['reviewer'] = 'Rev2'
        reviewer.insert()

    def tearDown(self):
        self.env.shutdown()

    def test_get_code_review_users(self):
        self.assertEqual(3, len(get_users(self.env)))

    def test_add_users_to_data_dict_no_review(self):
        data = {}
        add_users_to_data(self.env, 0, data)
        self.assertTrue('users' in data)
        self.assertEqual(3, len(data['users']))
        # There is no review so we have no assigned users.
        self.assertTrue('assigned_users' in data)
        self.assertEqual(0, len(data['assigned_users']))

        self.assertTrue('unassigned_users' in data)
        self.assertEqual(3, len(data['unassigned_users']))
        self.assertTrue('emptyList' in data)
        self.assertEqual(0, data['emptyList'])

    def test_add_users_to_data_dict(self):
        data = {}
        add_users_to_data(self.env, 1, data)
        self.assertTrue('users' in data)
        self.assertEqual(3, len(data['users']))
        # There is a review so we have assigned users.
        self.assertTrue('assigned_users' in data)
        self.assertEqual(2, len(data['assigned_users']))

        self.assertTrue('unassigned_users' in data)
        self.assertEqual(1, len(data['unassigned_users']))
        self.assertTrue('emptyList' in data)
        self.assertEqual(0, data['emptyList'])

    def test_test_add_users_to_data_dict_prepopulated(self):
        # data contains the list of users. It shouldn't be changed here.
        # Note that these users are different than the ones in the other tests.
        usr_lst = [item[0] for item in names if item[1] == 1]
        data = {'users': usr_lst}
        add_users_to_data(self.env, 1, data)
        self.assertTrue('users' in data)
        self.assertEqual(4, len(data['users']))
        for usr in data['users']:
            self.assertIn(usr, usr_lst)


class TestCreateCodeReview(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'codereview.model.*',
                                                             'codereview.peerreviewnew.*',
                                                             'codereview.peerreviewmain.*',
                                                             'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(cls.env).environment_created()
        _add_permissions(cls.env)
        cls.plugin = NewReviewModule(cls.env)
        cls.req = Mock(href=Mock(), perm=MockPerm())
        cls.req.authname = 'Tester'

        cls.req.args = {
            'Name': 'review_name',
            'Notes': 'review_notes',
            'project': 'review_project',
            'user': ['Rev1', 'Rev2'],
            # 'file': 'path,file_revision,123,789'
        }

    @classmethod
    def tearDownClass(cls):
        cls.env.shutdown()

    def test_create_code_review(self):
        """Test creation of a new review."""
        # TODO: do the same for followup reviews
        review_id = self.plugin.createCodeReview(self.req, 'create')
        self.assertEqual(1, review_id)
        review = PeerReviewModel(self.env, review_id)
        self.assertTrue(isinstance(review, PeerReviewModel))
        items = [
            [u'review_name', 'name'],
            [u'review_notes', 'notes'],
            [u'review_project', 'project'],
            [u'Tester', 'owner'],
            [u'new', 'status'],
            [0, 'parent_id']
        ]
        for item in items:
            self.assertEqual(item[0], review[item[1]])
        rm = PeerReviewerModel(self.env)
        rm.clear_props()
        rm['review_id'] = review_id
        reviewers = list(rm.list_matching_objects())
        self.assertEqual(2, len(reviewers))
        for rev in reviewers:
            self.assertEqual(1, rev['review_id'])
            self.assertTrue(rev['reviewer'] in ['Rev1', 'Rev2'])
            self.assertEqual(u'new', rev['status'])


def test_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestCreateFileHashId))
    suite.addTest(unittest.makeSuite(TestNewReviewModule))
    suite.addTest(unittest.makeSuite(TestUserHandling))
    suite.addTest(unittest.makeSuite(TestCreateCodeReview))

    return suite
