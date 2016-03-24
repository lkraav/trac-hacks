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
from string import Template
from trac import util
from trac.core import Component, implements, TracError
from trac.config import ListOption
from trac.mimeview import Context
from trac.resource import Resource
from trac.util import format_date
from trac.util.text import CRLF
from trac.web.chrome import INavigationContributor, add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to, format_to_html
from model import get_users, Comment, \
    PeerReviewerModel, PeerReviewModel, ReviewFileModel, ReviewDataModel
from peerReviewMain import add_ctxt_nav_items, web_context_compat
from tracgenericworkflow.api import IWorkflowTransitionListener, ResourceWorkflowSystem

try:
    from trac.web.chrome import web_context
except ImportError:
    web_context = web_context_compat

def review_is_finished(config, review):
    """A finished review may only be reopened by a manager or admisnistrator

    :param config: Trac config object
    :param review: review object

    :return True if review is in one of the terminal states
    """
    finish_states = config.getlist("peer-review", "terminal_review_states")
    return review['status'] in finish_states


def review_is_locked(config, review, authname=""):
    """For a locked review a user can't change his voting
    :param config: Trac config object
    :param review: review object
    :authname: login name of user

    :return True if review is in lock state, usually 'reviewed'.

    authname may be an empty string to check if a review is in the lock state at all.
    If not empty the review is not locked for the user with the given login name.
    """
    if review['owner'] == authname:
        return False

    lock_states = config.getlist("peer-review", "reviewer_locked_states")
    return review['status'] in lock_states


class PeerReviewView(Component):
    """Displays a summary page for a review.

    === The following configuration options may be set:

    [[TracIni(peer-review)]]
    """
    implements(IRequestHandler, INavigationContributor, IWorkflowTransitionListener)

    ListOption("peer-review", "terminal_review_states", ['closed', 'approved', 'disapproved'],
               doc="Ending states for a review. Only an administrator may force a review to leave these states. "
                   "Reviews in one of these states may not be modified.")

    ListOption("peer-review", "reviewer_locked_states", ['reviewed'],
               doc="A reviewer may no longer comment on reviews in one of the given states. The review owner still "
                   "may comment. Used to lock a review against modification after all reviewing persons have "
                   "finished their task.")

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
        return req.path_info == '/peerReviewView'

    def process_request(self, req):
        def get_review_by_id(review_id):
            """Get a PeerReviewModel for the given review id and prepare some additional data used by the template"""
            review = PeerReviewModel(self.env, review_id)
            review.html_notes = format_to_html(self.env, Context.from_request(req), review['notes'])
            review.date = format_date(review['created'])
            return review
        def get_files_for_review_id(review_id, comments=False):
            """Get all files belonging to the given review id. Provide the number of comments if asked for."""
            rfm = ReviewFileModel(self.env)
            rfm.clear_props()
            rfm['review_id'] = review_id
            rev_files = list(rfm.list_matching_objects())
            if comments:
                for f in rev_files:
                    f.num_comments = len(Comment.select_by_file_id(self.env, f['file_id']))
                    my_comment_data = ReviewDataModel.comments_for_file_and_owner(self.env, f['file_id'], req.authname)
                    f.num_notread = f.num_comments - len([c_id for c_id, t, dat in my_comment_data if t == 'read'])
            return rev_files

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

        data['review_files'] = get_files_for_review_id(review_id, True)
        data['users'] = get_users(self.env)

        review = get_review_by_id(review_id)
        data['review'] = review

        # A finished review can't be changed anymore except by a manager
        data['is_finished'] = review_is_finished(self.env.config, review)
        # A user can't change his voting for a reviewed review
        data['review_locked'] = review_is_locked(self.env.config, review, req.authname)
        # Used to indicate that a review is done. 'review_locked' is not suitable because it is false for the
        # author of a review even when the review is done.
        data['review_done'] = review_is_locked(self.env.config, review)

        # Parent review if any
        if review['parent_id'] != 0:
            data['parent_review'] = get_review_by_id(review['parent_id'])
            rev_files = get_files_for_review_id(review_id, False)
            data['parent_files'] = rev_files

            # Map files to parent files. Key is current file id, value is parent file object

            def get_parent_file(rfile, par_review_id, par_files):
                fid = u"%s%s%s" % (rfile['path'], rfile['line_start'], rfile['line_end'])
                for f in par_files:
                    tmp = u"%s%s%s" % (f['path'], f['line_start'], f['line_end'])
                    if tmp == fid:
                        return f
                return None

            file_map = {}
            for f in data['review_files']:
                file_map[f['file_id']] = get_parent_file(f, review['parent_id'], rev_files)
            data['file_map'] = file_map

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

        self.create_ticket_data(req, data)
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
        add_stylesheet(req, 'common/css/ticket.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_ctxt_nav_items(req)

        return 'peerReviewView.html', data, None

    desc = u"""
Review [/peerReviewView?Review=${review_id} ${review_name}] is finished.
=== Review

||= Name =|| ${review_name} ||
||= ID =|| ${review_id} ||
[[br]]
**Review Notes:**
${review_notes}

=== Files
||= File name =||= Comments =||
"""

    def create_ticket_data(self, req, data):
        """Create the ticket description for tickets created from the review page"""
        txt = u""
        review = data['review']
        tmpl = Template(self.desc)
        txt = tmpl.substitute(review_name=review['name'], review_id=review['review_id'],
                                   review_notes="")  #review['notes'])

        try:
            for f in data['review_files']:
                txt += u"||[/peerReviewPerform?IDFile=%s %s]|| %s ||%s" % \
                       (f['file_id'], f['path'], f.num_comments, CRLF)
        except KeyError:
            pass

        data['ticket_desc_wiki'] = self.create_preview(req, txt)
        data['ticket_desc'] = txt
        data['ticket_summary'] = u'Problems with Review "%s"'% review['name']

    def create_preview(self, req, text):
        resource = Resource('peerreview')
        context = web_context(req, resource)
        return format_to_html(self.env, context, text)
