#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

# Provides functionality for view code review page
# Works with peerReviewView.html

import itertools

from trac import util
from trac.core import Component, implements, TracError
from trac.mimeview import Context
from trac.resource import Resource
from trac.util import format_date
from trac.web.chrome import INavigationContributor, add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to_html
from model import get_users, Comment, \
    PeerReviewerModel, PeerReviewModel, ReviewFileModel
from peerReviewMain import add_ctxt_nav_items
from tracgenericworkflow.api import IWorkflowTransitionListener, ResourceWorkflowSystem


def review_is_finished(review):
    """A finished review may only be reopened by a manger"""
    return review['status'] in ['closed', 'approved', 'disapproved']

def review_is_locked(review):
    """For a locked review a iser can't change his voting"""
    return review['status'] == 'reviewed'


class PeerReviewView(Component):
    """Displays a summary page for a review."""
    implements(IRequestHandler, INavigationContributor, IWorkflowTransitionListener)

    number = -1
    files = []

    # IWorkflowTransitionListener

    def object_transition(self, res_wf_state, resource, action, old_state, new_state):
        if resource.realm == 'peerreviewer':
            reviewer = PeerReviewerModel(self.env, resource.id)
            reviewer['status'] = new_state
            reviewer.save_changes(author=res_wf_state.authname)
        elif resource.realm == 'peerreview':
            review = PeerReviewModel(self.env, resource.id)
            review.change_status(new_state, res_wf_state.authname)

    # INavigationContributor

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            return req.path_info == '/peerReviewView'
        return False

    def process_request(self, req):

        req.perm.require('CODE_REVIEW_DEV')

        data = {}
        # check to see if the user is a manager of this page or not
        if 'CODE_REVIEW_MGR' in req.perm:
            data['manager'] = True

        # review_id argument checking
        review_id = req.args.get('Review')
        if review_id is None or not review_id.isdigit():
            raise TracError(u"Invalid review ID supplied - unable to load page.")

        if req.method == 'POST':
            if req.args.get('resubmit'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id))
            elif req.args.get('followup'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id, followup=1))
            elif req.args.get('modify'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id, modify=1))

        rfm = ReviewFileModel(self.env)
        rfm.clear_props()
        rfm['review_id'] = review_id
        rev_files = list(rfm.list_matching_objects())
        for f in rev_files:
            f.num_comments = len(Comment.select_by_file_id(self.env, f['file_id']))

        data['review_files'] = rev_files
        data['users'] = get_users(self.env)

        review = PeerReviewModel(self.env, review_id)
        review.html_notes = format_to_html(self.env, Context.from_request(req), review['notes'])
        review.date = format_date(review['creation_date'])
        data['review'] = review

        # A finished review can't be changed anymore except by a manager
        data['is_finished'] = review_is_finished(review)
        # A user can't chnage his voting for a reviewed review
        data['review_locked'] = review_is_locked(review)

        # Parent review if any
        if review['parent_id'] != 0:
            par_review = PeerReviewModel(self.env, review['parent_id'])
            par_review.html_notes = format_to_html(self.env, Context.from_request(req), par_review['notes'])
            par_review.date = format_date(par_review['creation_date'])
            data['parent_review'] = par_review

        # Figure out whether I can vote on this review or not. This is used to decide in the template
        # if the reviewer actions should be shown. Note that this is legacy stuff going away later.
        #
        # TODO: remove this and use a better solution
        rm = PeerReviewerModel(self.env)
        rm.clear_props()
        rm['review_id'] = review_id
        reviewers = list(rm.list_matching_objects())
        for rev in reviewers:
            if rev['reviewer'] == req.authname:
                break
        data['reviewer'] = reviewers

        url = '.'

        # Actions for a reviewer. Each reviewer marks his progress on a review. The author
        # can see this progress in the user list. The possible actions are defined in trac.ini
        # as a workflow in [peerreviewer-resource_workflow]
        realm = 'peerreviewer'
        res = None

        for reviewer in reviewers:
            if reviewer['reviewer'] == req.authname:
                res = Resource(realm, str(reviewer['reviewer_id']))  # id must be a string
                if not data['is_finished'] and not data['review_locked']:
                    data['canivote'] = True
                break
        if res:
            data['reviewer_workflow'] = ResourceWorkflowSystem(self.env).\
                get_workflow_markup(req, url, realm, res, {'redirect': req.href.peerReviewView(Review=review_id)})

        # Actions for the author of a review. The author may approve, disapprove or close a review.
        # The possible actions are defined in trac.ini as a workflow in [peerreview-resource_workflow]
        realm = 'peerreview'
        res = Resource(realm, str(review['review_id']))  # Must be a string
        data['workflow'] = ResourceWorkflowSystem(self.env).\
            get_workflow_markup(req, url, realm, res, {'redirect': req.href.peerReviewView(Review=review_id)})

        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_ctxt_nav_items(req)

        return 'peerReviewView.html', data, None
