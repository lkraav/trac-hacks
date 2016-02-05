#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which 
# you should have received as part of this distribution.
#
# Author: Team5
#

# Provides functionality to create a new code review.
# Works with peerReviewNew.html

import itertools
import time

from trac import util
from trac.core import Component, implements, TracError
from trac.web.chrome import INavigationContributor, add_javascript, add_script_data, \
    add_warning, add_notice, add_stylesheet
from trac.web.main import IRequestHandler

from CodeReviewStruct import *
from model import ReviewFile, Review, Reviewer, get_users, Comment
from peerReviewMain import add_ctxt_nav_items


def java_string_hashcode(s):
    # See: http://garage.pimentech.net/libcommonPython_src_python_libcommon_javastringhashcode/
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def create_file_hash_id(f):
    return 'id%s' % java_string_hashcode("%s,%s,%s,%s" % (f.path, f.version, f.start, f.end))


def add_users_to_data(env, reviewID, data):
    """
    If data['user'] doesn't exist this function will query the list of available users.

    :param env:
    :param reviewID:
    :param data:
    :param all_users
    :return:
    """
    if 'users' not in data:
        data['users'] = get_users(env)
    all_users = data['users']

    # get code review data and populate
    reviewers = Reviewer.select_by_review_id(env, reviewID)
    popUsers = []
    for reviewer in reviewers:
        popUsers.append(reviewer.reviewer)
    data['assigned_users'] = popUsers

    # Figure out the users that were not included
    # in the previous code review so that they can be
    # added to the dropdown to select more users
    # (only check if all users were not included in previous code review)
    notUsers = []
    if len(popUsers) != len(all_users):
        notUsers = list(set(all_users)-set(popUsers))
        data['emptyList'] = 0
    else:
        data['emptyList'] = 1

    data['unassigned_users'] = notUsers


class NewReviewModule(Component):
    implements(IRequestHandler, INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return []

    # IRequestHandler methods
    def match_request(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            return req.path_info == '/peerReviewNew'
        return False

    def process_request(self, req):

        req.perm.require('CODE_REVIEW_DEV')

        if req.method == 'POST':
            oldid = req.args.get('oldid')
            if req.args.get('create'):
                if oldid:
                    # Automatically close the review we resubmitted from
                    review = Review(self.env, oldid)
                    review.status = "Closed"
                    review.update()
                    add_notice(req, "Review '%s' (#%s) was automatically closed." % (review.name, oldid))
                returnid = self.createCodeReview(req)
                #If no errors then redirect to the viewCodeReview page
                req.redirect(self.env.href.peerReviewView() + '?Review=' + str(returnid))
            if req.args.get('createfollowup'):
                returnid = self.createCodeReview(req)
                #If no errors then redirect to the viewCodeReview page
                req.redirect(self.env.href.peerReviewView(Review=returnid))
            if req.args.get('save'):
                self.save_changes(req)
                req.redirect(self.env.href.peerReviewView(Review=oldid))
            if req.args.get('cancel'):
                req.redirect(self.env.href.peerReviewView(Review=oldid))

        data = {}
        data['users'] = get_users(self.env)

        reviewID = req.args.get('resubmit')

        # if we tried resubmitting and the reviewID is not a valid number or not a valid code review, error
        review = Review(self.env, reviewID)
        if reviewID and (not reviewID.isdigit() or not review):
            raise TracError("Invalid resubmit ID supplied - unable to load page correctly.", "Resubmit ID error")

        # if we are resubmitting a code review and we are the author or the manager
        if reviewID and (review.author == req.authname or 'CODE_REVIEW_MGR' in req.perm):
            data['new'] = "no"
            data['oldid'] = reviewID

            add_users_to_data(self.env, reviewID, data)

            rfiles = ReviewFile.select_by_review(self.env, reviewID)
            popFiles = []
            # Set up the file information
            for f in rfiles:
                # This id is used by the hacascript code to find duplicate entries.
                f.element_id = create_file_hash_id(f)
                popFiles.append(f)

            data['name'] = review.name
            data['notes'] = "Review based on ''%s'' (resubmitted)." % review.name

            data['prevFiles'] = popFiles

        #if we resubmitting a code review, and are neither the author and the manager
        elif reviewID and not review.author == req.authname and not 'CODE_REVIEW_MGR' in req.perm:
            raise TracError("You need to be a manager or the author of this code review to resubmit it.", "Access error")
        #if we are not resubmitting
        else:
            data['new'] = "yes"

        data['cycle'] = itertools.cycle
        data['followup'] = req.args.get('followup')

        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_script_data(req, {'repo_browser': self.env.href.peerReviewBrowser()})
        add_javascript(req, "hw/js/peer_review_new.js")
        add_javascript(req, 'hw/js/peer_user_list.js')
        add_ctxt_nav_items(req)
        return 'peerReviewNew.html', data, None

    # Takes the information given when the page is posted
    # and creates a new code review struct in the database
    # and populates it with the information.  Also creates
    # new reviewer structs and file structs for the review.
    def createCodeReview(self, req):
        review = Review(self.env)
        review.author = req.authname
        review.status = 'Open for review'
        review.raw_date = int(time.time())
        review.name = req.args.get('Name')
        review.notes = req.args.get('Notes')
        if req.args.get('followup'):
            review.parent_id = req.args.get('oldid', 0)
        review.insert()
        id_ = review.review_id
        self.log.debug('New review created: %s', id_)

        # loop here through all the reviewers
        # and create new reviewer structs based on them
        user = req.args.get('user')
        if not type(user) is list:
            user = [user]
        for name in user:
            if name != "":
                reviewer = Reviewer(self.env)
                reviewer.review_id = id_
                reviewer.reviewer = name
                reviewer.status = 0
                reviewer.vote = "-1"
                reviewer.insert()

        # loop here through all included files
        # and create new file structs based on them
        files = req.args.get('file')
        if not type(files) is list:
            files = [files]
        for item in files:
            if item != "":
                segment = item.split(',')
                rfile = ReviewFile(self.env)
                rfile.review_id = id_
                rfile.path = segment[0]
                if req.args.get('followup'):
                    rfile.version = req.args.get('revision', 0)
                else:
                    rfile.version = segment[1]
                rfile.start = segment[2]
                rfile.end = segment[3]
                rfile.insert()
        return id_

    def save_changes(self, req):
        def file_is_commented(author):
            rfiles = ReviewFile.select_by_review(self.env, review.review_id)
            for f in rfiles:
                comments = [c for c in Comment.select_by_file_id(self.env, f.file_id) if c.author == author]
                if comments:
                    return True
            return False

        review = Review(self.env, req.args.get('oldid'))
        review.name = req.args.get('Name')
        review.notes = req.args.get('Notes')
        review.update()

        user = req.args.get('user')
        if not type(user) is list:
            user = [user]
        data = {}
        add_users_to_data(self.env,review.review_id, data)
        # Handle new users if any
        new_users = list(set(user) - set(data['assigned_users']))
        for name in new_users:
            if name != "":
                reviewer = Reviewer(self.env)
                reviewer.review_id = review.review_id
                reviewer.reviewer = name
                reviewer.status = 0
                reviewer.vote = "-1"
                reviewer.insert()
        # Handle removed users if any
        rem_users = list(set(data['assigned_users']) - set(user))
        for name in rem_users:
            if name != "":
                reviewer = Reviewer(self.env, review.review_id, name)
                if reviewer.vote != -1:
                    add_warning(req, "User '%s' already voted. Not removed from review '#%s'",
                                name, review.review_id)
                    continue
                if file_is_commented(name):
                    add_warning(req, "User '%s' already commented a file. Not removed from review '#%s'",
                                name, review.review_id)
                    continue
                reviewer.delete()
