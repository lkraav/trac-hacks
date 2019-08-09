# -*- coding: utf-8 -*-

import unittest
from trac.web import Href
from trac.test import EnvironmentStub, Mock, MockPerm
from codereview.model import PeerReviewModel, PeerReviewModelProvider
from codereview.tracgenericworkflow.api import  ResourceWorkflowSystem
from codereview.tracgenericworkflow.model import GenericWorkflowModelProvider


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

    with env.db_transaction as db:
        cursor = db.cursor()
        for rev in revs:
            cursor.execute("INSERT INTO peerreview (owner, status, name, notes, parent_id) "
                           "VALUES (%s,%s,%s,%s,%s)", rev)


class TestReviewModel(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*', 'codereview.*'])
        PeerReviewModelProvider(self.env).environment_created()
        GenericWorkflowModelProvider(self.env).environment_created()  # Needed for creating the workflow table
        _prepare_review_data(self.env)
        self.plugin = ResourceWorkflowSystem(self.env)
        self.req = Mock(href=Href(''), perm=MockPerm(), redirect=lambda x: x)
        self.req.authname = 'Tester'
        self.req.path_info = '/workflowtransition'

    def tearDown(self):
        self.env.shutdown()

    def test_get_review(self):
        rm = PeerReviewModel(self.env, 1)
        self.assertTrue(isinstance(rm, PeerReviewModel))
        self.assertTrue(rm.exists)
        self.assertEqual('name1', rm['name'])
        self.assertEqual('bar', rm['status'])
        self.assertEqual('note1', rm['notes'])
        self.assertEqual('Rev1', rm['owner'])

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
        rev = revs[0]
        self.assertEqual('name2', rev['name'])
        self.assertEqual('closed', rev['status'])
        self.assertEqual('note2', rev['notes'])
        self.assertEqual('Rev1', rev['owner'])


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
        all_revs = list(PeerReviewModel.select_all_reviews(self.env))
        self.assertEqual(5, len(all_revs))

    def test_select_all_reviews(self):
        all_revs = list(PeerReviewModel.select_all_reviews(self.env))
        self.assertEqual(4, len(all_revs))
        # we have 4 different notes. This is an easy check if we got different objects.
        seen = {}
        for rev in all_revs:
            seen[rev['notes']] = rev
        self.assertEqual(4, len(seen))
        # Same for name
        seen = {}
        for rev in all_revs:
            seen[rev['name']] = rev
        self.assertEqual(4, len(seen))
        self.assertEqual('note2', seen['name2']['notes'])
        self.assertEqual('Rev1', seen['name2']['owner'])
        self.assertEqual('closed', seen['name2']['status'])


def review_model_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestReviewModel))

    return suite
