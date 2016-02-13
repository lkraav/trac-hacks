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
from model import Review, ReviewFile, Reviewer, Vote, get_threshold, get_users, Comment, \
    PeerReviewerModel, PeerReviewModel
from peerReviewMain import add_ctxt_nav_items
from tracgenericworkflow.api import IWorkflowTransitionListener, ResourceWorkflowSystem


class ViewReviewModule(Component):
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
            review['status'] = new_state
            review.save_changes(author=res_wf_state.authname)

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
            manager = True
        else:
            manager = False

        # review_id argument checking
        review_id = req.args.get('Review')
        if review_id is None or not review_id.isdigit():
            raise TracError(u"Invalid review ID supplied - unable to load page.")

        if req.method == 'POST':
            if req.args.get('approved'):
                self.vote("1", review_id, req, req.authname)  # This call will redirect
            elif req.args.get('notapproved'):
                self.vote("0", review_id, req, req.authname)  # This call will redirect
            elif req.args.get('close'):
                self.close_review(req, review_id, manager)
            elif req.args.get('inclusion'):
                self.submit_for_inclusion(req, review_id)
            elif req.args.get('ManagerChoice'):
                # process state (Open for review, ready for inclusion, etc.) change by manager
                mc = req.args.get('ManagerChoice')
                if mc == "new" or mc == "reviewed" or mc == "forinclusion" or mc == "closed":
                    self.manager_change_status(req, review_id, mc)
            elif req.args.get('resubmit'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id))
            elif req.args.get('followup'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id, followup=1))
            elif req.args.get('modify'):
                req.redirect(self.env.href.peerReviewNew(resubmit=review_id, modify=1))

        rev_files = ReviewFile.select_by_review(self.env, review_id)
        for f in rev_files:
            f.num_comments = len(Comment.select_by_file_id(self.env, f.file_id))

        data['review_files'] = rev_files
        data['users'] = get_users(self.env)

        review = PeerReviewModel(self.env, review_id)
        review.html_notes = format_to_html(self.env, Context.from_request(req), review['notes'])
        review.date = format_date(review['creation_date'])
        data['review'] = review
        if review['parent_id'] != 0:
            par_review = PeerReviewModel(self.env, review['parent_id'])
            par_review.date = format_date(par_review['creation_date'])
            data['parent_review'] = par_review

        data['manager'] = manager

        # Figure out whether I can vote on this review or not. This is used to decide in the template
        # if the reviewer actions should be shown. Note that this is legacy stuff going away later.
        #
        # TODO: remove this and use a better solution
        if Reviewer.select_by_review_id(self.env, review_id, req.authname):
            data['canivote'] = True
        else:
            data['canivote'] = False

        reviewers = Reviewer.select_by_review_id(self.env, review_id)
        data['reviewer'] = reviewers

        url = '.'

        # Actions for a reviewer. Each reviewer marks his progress on a review. The author
        # can see this progress in the user list. The possible actions are defined in trac.ini
        # as a workflow in [peerreviewer-resource_workflow]
        realm = 'peerreviewer'
        res = None
        for reviewer in reviewers:
            if reviewer.reviewer == req.authname:
                res = Resource(realm, str(reviewer.id))  # id must be a string
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
