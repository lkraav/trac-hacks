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
from trac.web.chrome import INavigationContributor, add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to_html

from dbBackend import *
from model import Review, ReviewFile, Reviewer, Vote, get_threshold
from peerReviewMain import add_ctxt_nav_items

class ViewReviewModule(Component):
    """Displays a summary page for a review."""
    implements(IRequestHandler, INavigationContributor)

    number = -1
    files = []

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

        # reviewID argument checking
        reviewID = req.args.get('Review')
        if reviewID is None or not reviewID.isdigit():
            raise TracError(u"Invalid review ID supplied - unable to load page.")

        if req.method == 'POST':
            if req.args.get('approved'):
                self.vote("1", reviewID, req, req.authname)  # This call will redirect
            elif req.args.get('notapproved'):
                self.vote("0", reviewID, req, req.authname)  # This call will redirect
            elif req.args.get('close'):
                self.close_review(req, reviewID, manager)
            elif req.args.get('inclusion'):
                self.submit_for_inclusion(req, reviewID)
            elif req.args.get('ManagerChoice'):
                # process state (Open for review, ready for inclusion, etc.) change by manager
                mc = req.args.get('ManagerChoice')
                if mc == "Open for review" or mc == "Reviewed" or mc == "Ready for inclusion" or mc == "Closed":
                    self.manager_change_status(req, reviewID, mc)
            elif req.args.get('resubmit'):
                req.redirect(self.env.href.peerReviewNew(resubmit=reviewID))

        # set up to display the files that are in this review
        db = self.env.get_read_db()
        dbBack = dbBackend(db)

        rev_files = ReviewFile.select_by_review(self.env, reviewID)
        for f in rev_files:
            f.num_comments = len(dbBack.getCommentsByFileID(f.file_id))

        data['review_files'] = rev_files
        data['users'] = dbBack.getPossibleUsers()

        review = Review(self.env, reviewID)

        data['notes'] = format_to_html(self.env, Context.from_request(req), review.notes)

        votes = Vote(self.env, reviewID)
        # set up the fields that will be displayed on the page
        data['myname'] = req.authname
        data['review'] = review
        data['manager'] = manager
        data['votes'] = votes

        # figure out whether I can vote on this review or not
        entry = Reviewer.select_by_review_id(self.env, reviewID, req.authname)
        if entry:
            data['canivote'] = True
            data['myvote'] = entry.vote
        else:
            data['canivote'] = False

        # display vote summary only if I have voted or am the author/manager,
        # or if the review is "Ready for inclusion" or "Closed

        if review.author == req.authname or manager or \
                (entry and entry.vote != '-1') or \
                review.status == "Closed" or review.status == "Ready for inclusion":
            data['viewvotesummary'] = True
        else:
            data['viewvotesummary'] = False

        rvs = []  # reviewer/vote pairs
        reviewers = Reviewer.select_by_review_id(self.env, reviewID)
        newrvpair = []

        # if we are the manager, list who has voted and what their vote was.
        # if we are the author, list who has voted and who has not.
        # if we are neither, list the users who are participating in this review.
        if manager:
            self.env.log.debug("I am a manager")
            for reviewer in reviewers:
                newrvpair.append(reviewer.reviewer)
                if reviewer.vote == -1:
                    newrvpair.append("Not voted")
                elif reviewer.vote == 0:
                    newrvpair.append("No")
                elif reviewer.vote == 1:
                    newrvpair.append("Yes")
                rvs.append(newrvpair)
                newrvpair = []
        elif review.author == req.authname:
            self.env.log.debug("I am the author")
            for reviewer in reviewers:
                newrvpair.append(reviewer.reviewer)
                if reviewer.vote == -1:
                    newrvpair.append("Not voted")
                else:
                    newrvpair.append("Voted")
                rvs.append(newrvpair)
                newrvpair = []
        else:
            self.env.log.debug("I am somebody else")
            for reviewer in reviewers:
                newrvpair.append(reviewer.reviewer)
                rvs.append(newrvpair)
                newrvpair = []

        data['rvs'] = rvs
        data['rvsLength'] = len(rvs)

        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_ctxt_nav_items(req)
        return 'peerReviewView.html', data, None

    # If user has not voted for this review and is a voting member, and attempts
    # to vote, change the vote type in the review entry struct in the database
    # and reload the page.
    def vote(self, one_or_zero, number, req, myname):
        reviewEntry = Reviewer.select_by_review_id(self.env, number, myname)
        if reviewEntry:
            reviewEntry.vote = one_or_zero
            reviewEntry.update()

        reviewID = req.args.get('Review')
        review = Review(self.env, reviewID)

        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        # TODO: there is some code in admin.py calculsating a similar threshold. Try to unify this.
        votes = Vote(self.env, reviewID)
        voteyes = votes.yes
        voteno = votes.no
        notvoted = votes.pending
        total_votes_possible = float(voteyes) + float(voteno) + float(notvoted)
        threshold = float(get_threshold(self.env))/100

        # recalculate vote ratio, while preventing divide by zero tests, and change status if necessary
        if total_votes_possible != 0:
            vote_ratio = float(voteyes)/float(total_votes_possible)
            if vote_ratio >= threshold:
                review.status = "Reviewed"
            else:
                review.status = "Open for review"
            review.update()
        req.redirect(self.env.href.peerReviewView(Review=reviewID))

    # If it is confirmed that the user is the author of this review and they
    # have attempted to submit for inclusion, change the status of this review
    # to "Ready for inclusion" and reload the page.
    def submit_for_inclusion(self, req, number):
        review = Review(self.env, number)
        if review.author == req.authname:
            if review.status == "Reviewed":
                review.status = "Ready for inclusion"
                review.update()
                req.redirect(self.env.href.peerReviewView(Review=number))

    # If the user is confirmed to be the author or manager and tries to close
    # this review, close it by changing the status of the review to "Closed."
    def close_review(self, req, number, manager):
        review = Review(self.env, number)
        # this option available if you are the author or manager of this code review
        if review.author == req.authname or manager:
            review.status = "Closed"
            review.update()
            req.redirect(self.env.href.peerReviewView(Review=number))

    # It has already been confirmed that this user is a manager, so this routine
    # just changes the status of the review to the ne status specified by the manager.
    def manager_change_status(self, req, number, new_status):
        review = Review(self.env, number)
        review.status = new_status
        review.update()
        req.redirect(self.env.href.peerReviewView(Review=number))
