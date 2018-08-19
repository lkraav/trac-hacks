# -*- coding: utf-8 -*-

import unittest
from trac.web import Href
from trac.test import EnvironmentStub, Mock, MockPerm
from ..model import  PeerReviewModel, PeerReviewModelProvider
from ..tracgenericworkflow.api import  ResourceWorkflowSystem
from ..tracgenericworkflow.model import GenericWorkflowModelProvider


__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


def _prepare_review_data(env):
    # owner, status, name, notes, parent_is
    revs = [
        ['Rev1', 'bar', 'name1', 'note1', 0],
        ['Rev1', 'closed', 'name2', 'note2', 0],
        ['Rev2', 'bar', 'name3', 'note3', 1],
        ['Rev3', 'foo', 'name4', 'note4', 2]
    ]

    @env.with_transaction()
    def do_insert(db):
        for rev in revs:
            cursor = db.cursor()
            cursor.execute("INSERT INTO peerreview (owner, status, name, notes, parent_id) "
                           "VALUES (%s,%s,%s,%s,%s)", rev)


class TestReviewModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env = EnvironmentStub(default_data=True, enable=['trac.*', 'codereview.*'])
        PeerReviewModelProvider(cls.env).environment_created()
        GenericWorkflowModelProvider(cls.env).environment_created()  # Needed for creating the workflow table
        _prepare_review_data(cls.env)
        cls.plugin = ResourceWorkflowSystem(cls.env)
        cls.req = Mock(href=Href(''), perm=MockPerm(), redirect=lambda x: x)
        cls.req.authname = 'Tester'
        cls.req.path_info = '/workflowtransition'

    @classmethod
    def tearDownClass(cls):
        cls.env.shutdown()

    def test_get_review(self):
        rm = PeerReviewModel(self.env, 1)
        self.assertTrue(isinstance(rm, PeerReviewModel))
        self.assertTrue(rm.exists)

    def test_query_by_status(self):
        rm = PeerReviewModel(self.env)
        rm.clear_props()
        rm['status'] = 'bar'
        revs = list(rm.list_matching_objects())
        self.assertEqual(2, len(revs))
        rm = PeerReviewModel(self.env)
        rm.clear_props()
        rm['status'] = 'closed'
        revs = list(rm.list_matching_objects())
        self.assertEqual(1, len(revs))

    def test_query_by_owner(self):
        rm = PeerReviewModel(self.env)
        rm.clear_props()
        rm['owner'] = 'Rev1'
        revs = list(rm.list_matching_objects())
        self.assertEqual(2, len(revs))

    def test_change_note(self):
        rm = PeerReviewModel(self.env, 1)
        self.assertEqual(u'note1', rm['notes'])
        rm['notes'] = u'note1_changed'
        rm.save_changes()
        rm = PeerReviewModel(self.env, 1)
        self.assertEqual(u'note1_changed', rm['notes'])

    def test_review_workflow(self):
        self.req.args = {
            'id': '4',
            'res_realm': 'peerreview',
            'selected_action': 'approve'
        }
        rm = PeerReviewModel(self.env, 4)
        self.assertEqual('foo', rm['status'])
        # Do workflow transition
        self.plugin.process_request(self.req)
        rm_after = PeerReviewModel(self.env, 4)
        self.assertEqual('approved', rm_after['status'])

    def test_insert_new_review(self):
        rev = PeerReviewModel(self.env)
        rev['name'] = 'insert'
        rev['owner'] = 'Tester'
        rev.insert()
        # TODO: this will become an int in the future
        self.assertEqual(5, rev['review_id'])


def review_model_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestReviewModel))

    return suite
