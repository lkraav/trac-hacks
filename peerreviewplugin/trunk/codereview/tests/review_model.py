# -*- coding: utf-8 -*-

import unittest
from datetime import datetime
from trac.util.datefmt import to_datetime, to_utimestamp
from trac.web import Href
from trac.test import EnvironmentStub, Mock, MockPerm
from codereview.model import PeerReviewModel, PeerReviewModelProvider, ReviewFileModel
from codereview.tracgenericworkflow.api import  ResourceWorkflowSystem
from codereview.tracgenericworkflow.model import GenericWorkflowModelProvider


__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


def _prepare_review_data(env):
    # owner, status, name, notes, parent_id
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
        [1, '/foo/bar', 5, 100, '1234', 'new', None],
        [1, '/foo/bar2', 6, 101, '1234', 'new', None],
        [2, '/foo/bar', 5, 100, '1234', 'closed', None],
        [2, '/foo/bar2', 6, 101, '12346', 'closed', None],
        [2, '/foo/bar3', 7, 102, '12347', 'closed', None],
        [3, '/foo/bar2', 6, 101, '1234', 'new', None],
        [4, '/foo/bar', 5, 100, '1234', 'new', None],
        [4, '/foo/bar2', 6, 101, '1234', 'new', None],
        # File list data for several projects
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjFoo'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjFoo'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBar'],
        [0, '/foo/bar2', 6, 101, '12346', 'new', 'PrjBar'],
        [0, '/foo/bar3', 7, 102, '12347', 'new', 'PrjFoo'],
        [0, '/foo/bar/baz', 6, 101, '1234', 'new', 'PrjBar'],
        [0, '/foo/bar', 5, 100, '1234', 'new', 'PrjBaz'],
        [0, '/foo/bar2', 6, 101, '1234', 'new', 'PrjBaz'],
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
        rfm.insert()


class TestReviewModel(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*', 'codereview.*'])
        PeerReviewModelProvider(self.env).environment_created()
        GenericWorkflowModelProvider(self.env).environment_created()  # Needed for creating the workflow table
        _prepare_review_data(self.env)
        _prepare_file_data(self.env)
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

    def test_change_status(self):
        self.env.config.set("peerreview", "terminal_review_states", "closed, removed, obsolete")
        self.env.config.save()
        rev_pre = PeerReviewModel(self.env, 4)
        self.assertEqual('Rev3', rev_pre['owner'])
        self.assertEqual('foo', rev_pre['status'])
        files = list(ReviewFileModel.select_by_review(self.env, rev_pre['review_id']))
        self.assertEqual(2, len(files))
        for item in files:
            self.assertEqual('new', item['status'])

        # Change review to 'closed' which is a terminal state
        rev_pre.change_status('closed')
        rev = PeerReviewModel(self.env, 4)
        self.assertEqual('Rev3', rev['owner'])
        self.assertEqual('closed', rev['status'])
        # files must be closed now
        files = list(ReviewFileModel.select_by_review(self.env, rev['review_id']))
        self.assertEqual(2, len(files))
        for item in files:
            self.assertEqual('closed', item['status'])

        # Do it again to check if something toggles the status
        rev_pre = PeerReviewModel(self.env, 4)
        rev_pre.change_status('closed')
        rev = PeerReviewModel(self.env, 4)
        self.assertEqual('Rev3', rev['owner'])
        self.assertEqual('closed', rev['status'])
        # files must be closed now
        files = list(ReviewFileModel.select_by_review(self.env, rev['review_id']))
        self.assertEqual(2, len(files))
        for item in files:
            self.assertEqual('closed', item['status'])

        # Change to another terminal state
        rev_pre = PeerReviewModel(self.env, 4)
        rev_pre.change_status('removed')
        rev = PeerReviewModel(self.env, 4)
        self.assertEqual('Rev3', rev['owner'])
        self.assertEqual('removed', rev['status'])
        # files must have status 'removed' now
        files = list(ReviewFileModel.select_by_review(self.env, rev['review_id']))
        self.assertEqual(2, len(files))
        for item in files:
            self.assertEqual('removed', item['status'])

        # Change to a non-terminal state
        rev_pre = PeerReviewModel(self.env, 4)
        rev_pre.change_status('Baz')
        rev = PeerReviewModel(self.env, 4)
        self.assertEqual('Rev3', rev['owner'])
        self.assertEqual('Baz', rev['status'])
        # files must be 'new' now
        files = list(ReviewFileModel.select_by_review(self.env, rev['review_id']))
        self.assertEqual(2, len(files))
        for item in files:
            self.assertEqual('new', item['status'])


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

    def test_reviews_by_period(self):
        revs = PeerReviewModel.reviews_by_period(self.env,
                                                 to_utimestamp(to_datetime(datetime(2019, 3, 4))),
                                                 to_utimestamp(to_datetime(datetime(2019, 3, 14))))
        self.assertEqual(2, len(revs))
        # Reviews are ordered by 'created'
        self.assertEqual('Rev1', revs[0]['owner'])
        self.assertEqual('Rev2', revs[1]['owner'])

        revs = PeerReviewModel.reviews_by_period(self.env,
                                                 to_utimestamp(to_datetime(datetime(2019, 3, 4))),
                                                 to_utimestamp(to_datetime(datetime(2019, 3, 13))))
        self.assertEqual(1, len(revs))
        self.assertEqual('Rev1', revs[0]['owner'])
        revs = PeerReviewModel.reviews_by_period(self.env,
                                                 to_utimestamp(to_datetime(datetime(2019, 3, 4))),
                                                 to_utimestamp(to_datetime(datetime(2019, 4, 5))))
        self.assertEqual(3, len(revs))
        # Reviews are ordered by 'created'
        self.assertEqual('Rev1', revs[0]['owner'])
        self.assertEqual('Rev2', revs[1]['owner'])
        self.assertEqual('Rev3', revs[2]['owner'])

def review_model_suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TestReviewModel))

    return suite
