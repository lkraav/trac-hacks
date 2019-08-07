# -*- coding: utf-8 -*-

import unittest
from trac.admin.console import TracAdmin
from trac.web import Href
from trac.perm import PermissionError
from trac.test import EnvironmentStub, Mock, MockPerm
from ..model import  get_users, PeerReviewModel, PeerReviewerModel, PeerReviewModelProvider
from ..peerReviewNew import add_users_to_data, create_file_hash_id, NewReviewModule

__author__ = 'Cinc'

__copyright__ = "Copyright 2016"
__license__ = "BSD"

def _add_permissions(env):
    admin = TracAdmin()
    admin.env_set('Testenv', env)
    admin.onecmd("permission add Tester TICKET_VIEW")  # User not allowed to perform code reviews
    admin.onecmd("permission add Rev1 TRAC_ADMIN")
    admin.onecmd("permission add Rev2 CODE_REVIEW_DEV")
    admin.onecmd("permission add Rev3 CODE_REVIEW_MGR")
    admin.onecmd("permission add Rev1 RevGroup")
    admin.onecmd("permission add Rev2 RevGroup")


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

class TestComponent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'codereview.model.*',
                                                             'codereview.peerreviewnew.*',
                                                             'codereview.peerreviewmain.*',
                                                             'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(cls.env).environment_created()
        cls.plugin =  NewReviewModule(cls.env)
        cls.req = Mock(href=Mock(), perm=MockPerm())

    @classmethod
    def tearDownClass(cls):
        cls.env.shutdown()

    def test_get_active_navigation_item(self):
        self.assertEqual('peerReviewMain', self.plugin.get_active_navigation_item(self.req))

    def test_get_navigation_items(self):
        self.assertEqual(0, len(self.plugin.get_navigation_items(self.req)))


class TestUserHandling(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentStub(default_data=True,
                                  enable=['trac.*',
                                          'codereview.model.*',
                                          'codereview.peerreviewnew.*',
                                          'codereview.peerreviewmain.*',
                                          'codereview.tracgenericclass.*'])
        PeerReviewModelProvider(cls.env).environment_created()
        cls.plugin =  NewReviewModule(cls.env)
        _add_permissions(cls.env)
        reviewer = PeerReviewerModel(cls.env)
        reviewer['review_id'] = 1
        reviewer['reviewer'] = 'Rev1'
        reviewer.insert()
        reviewer = PeerReviewerModel(cls.env)
        reviewer['review_id'] = 1
        reviewer['reviewer'] = 'Rev2'
        reviewer.insert()

    @classmethod
    def tearDownClass(cls):
        cls.env.shutdown()

    def test_get_code_review_users(self):
        self.assertEqual(3,len(get_users(self.env)))

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
        # There is no review so we have no assigned users.
        self.assertTrue('assigned_users' in data)
        self.assertEqual(2, len(data['assigned_users']))

        self.assertTrue('unassigned_users' in data)
        self.assertEqual(1, len(data['unassigned_users']))
        self.assertTrue('emptyList' in data)
        self.assertEqual(0, data['emptyList'])


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
        cls.plugin =  NewReviewModule(cls.env)
        cls.req = Mock(href=Mock(), perm=MockPerm())
        cls.req.authname = 'Tester'

        cls.req.args={
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

def new_review_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestCreateFileHashId))
    suite.addTest(unittest.makeSuite(TestComponent))
    suite.addTest(unittest.makeSuite(TestUserHandling))
    suite.addTest(unittest.makeSuite(TestCreateCodeReview))

    return suite
