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
# Works with peerReviewView.cs

import itertools

from trac import util
from trac.core import Component, implements, TracError
from trac.mimeview import Context
from trac.web.chrome import INavigationContributor, add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to_html

from CodeReviewStruct import *
from dbBackend import *
from ReviewerStruct import *
from model import Review, ReviewFile

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
            TracError(u"Invalid review ID supplied - unable to load page.")

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

        # set up the fields that will be displayed on the page
        data['myname'] = req.authname
        data['voteyes'] = dbBack.getVotesByID("1", reviewID)
        data['voteno'] = dbBack.getVotesByID("0", reviewID)
        data['notvoted'] = dbBack.getVotesByID("-1", reviewID)
        data['total_votes_possible'] = float(data['voteyes']) + float(data['voteno']) + float(data['notvoted'])
        data['review'] = review
        data['manager'] = manager

        # figure out whether I can vote on this review or not
        entry = dbBack.getReviewerEntry(reviewID, data['myname'])
        if entry is not None:
            data['canivote'] = 1
            data['myvote'] = entry.Vote
        else:
            data['canivote'] = 0

        # display vote summary only if I have voted or am the author/manager,
        # or if the review is "Ready for inclusion" or "Closed
        data['viewvotesummary'] = 0
        if review.author == data['myname'] or manager or \
                (dbBack.getReviewerEntry(reviewID, data['myname']) is not None and
                 dbBack.getReviewerEntry(reviewID, data['myname']).Vote != '-1') or \
                review.status == "Closed" or review.status == "Ready for inclusion":
            data['viewvotesummary'] = 1
        else:
            data['viewvotesummary'] = 0

        rvs = []  # reviewer/vote pairs
        reviewers = dbBack.getReviewers(reviewID)
        newrvpair = []

        # if we are the manager, list who has voted and what their vote was.
        # if we are the author, list who has voted and who has not.
        # if we are neither, list the users who are participating in this review.
        if manager:
            self.env.log.debug("I am a manager")
            for reviewer in reviewers:
                newrvpair.append(reviewer.Reviewer)
                if reviewer.Vote == -1:
                    newrvpair.append("Not voted")
                elif reviewer.Vote == 0:
                    newrvpair.append("No")
                elif reviewer.Vote == 1:
                    newrvpair.append("Yes")
                rvs.append(newrvpair)
                newrvpair = []
        elif review.author == util.get_reporter_id(req):
            self.env.log.debug("I am the author")
            for reviewer in reviewers:
                newrvpair.append(reviewer.Reviewer)
                if reviewer.Vote == -1:
                    newrvpair.append("Not voted")
                else:
                    newrvpair.append("Voted")
                rvs.append(newrvpair)
                newrvpair = []
        else:
            self.env.log.debug("I am somebody else")
            for reviewer in reviewers:
                newrvpair.append(reviewer.Reviewer)
                rvs.append(newrvpair)
                newrvpair = []

        data['rvs'] = rvs
        data['rvsLength'] = len(rvs)

        # execute based on URL arguments
        if req.args.get('Vote') == 'yes':
            self.vote("1", reviewID, req, data['myname'])
        if req.args.get('Vote') == 'no':
            self.vote("0", reviewID, req, data['myname'])

        # process state (Open for review, ready for inclusion, etc.) change by manager
        mc = req.args.get('ManagerChoice')
        if mc == "Open for review" or mc == "Reviewed" or mc == "Ready for inclusion" or mc == "Closed":
            self.manager_change_status(mc, reviewID, req)

        if req.args.get('Close') == '1':
            self.close_review(reviewID, req, manager)

        if req.args.get('Inclusion') == '1':
            self.submit_for_inclusion(reviewID, req)

        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        return 'peerReviewView.html', data, None

    # If user has not voted for this review and is a voting member, and attempts
    # to vote, change the vote type in the review entry struct in the database
    # and reload the page.
    def vote(self, type, number, req, myname):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        reviewEntry = dbBack.getReviewerEntry(number, myname)
        if reviewEntry is not None:
            reviewEntry.Vote = type
            reviewEntry.save(db)

        reviewID = req.args.get('Review')
        review = dbBack.getCodeReviewsByID(reviewID)

        voteyes = dbBack.getVotesByID("1", reviewID)
        voteno = dbBack.getVotesByID("0", reviewID)
        notvoted = dbBack.getVotesByID("-1", reviewID)
        total_votes_possible = float(voteyes) + float(voteno) + float(notvoted)
        threshold = float(dbBack.getThreshold())/100

        # recalculate vote ratio, while preventing divide by zero tests, and change status if necessary
        if total_votes_possible != 0:
            vote_ratio = float(voteyes)/float(total_votes_possible)
            if vote_ratio >= threshold:
                review.Status = "Reviewed"
            else:
                review.Status = "Open for review"
            review.save(db)
        req.redirect(self.env.href.peerReviewView() + "?Review=" + reviewID)

    # If it is confirmed that the user is the author of this review and they
    # have attempted to submit for inclusion, change the status of this review
    # to "Ready for inclusion" and reload the page.
    def submit_for_inclusion(self, number, req):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        review = dbBack.getCodeReviewsByID(number)
        if review.Author == util.get_reporter_id(req):
            if review.Status == "Reviewed":
                review.Status = "Ready for inclusion"
                review.save(db)
                req.redirect(self.env.href.peerReviewView() + "?Review=" + number)

    # If the user is confirmed to be the author or manager and tries to close
    # this review, close it by changing the status of the review to "Closed."
    def close_review(self, number, req, manager):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        review = dbBack.getCodeReviewsByID(number)
        # this option available if you are the author or manager of this code review
        if review.Author == util.get_reporter_id(req) or manager:
            review.Status = "Closed"
            review.save(db)
            req.redirect(self.env.href.peerReviewView() + "?Review=" + number)

    # It has already been confirmed that this user is a manager, so this routine
    # just changes the status of the review to the type specified by the manager.
    def manager_change_status(self, type, number, req):
        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        review = dbBack.getCodeReviewsByID(number)
        review.Status = type
        review.save(db)
        req.redirect(self.env.href.peerReviewView() + "?Review=" + number)
