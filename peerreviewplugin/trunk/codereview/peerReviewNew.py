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
# Works with peerReviewNew.cs

import itertools
import time

from trac import util
from trac.core import Component, implements, TracError
from trac.web.chrome import INavigationContributor
from trac.web.main import IRequestHandler

from CodeReviewStruct import *
from dbBackend import *
from ReviewerStruct import *
from model import ReviewFile
from peerReviewMain import add_ctxt_nav_items

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

        data = {}

        db = self.env.get_db_cnx()
        dbBack = dbBackend(db)
        allUsers = dbBack.getPossibleUsers()

        reviewID = req.args.get('resubmit')
        data['oldid'] = -1

        # if we tried resubmitting and the reviewID is not a valid number or not a valid code review, error
        if reviewID is not None and (not reviewID.isdigit() or dbBack.getCodeReviewsByID(reviewID) is None):
            TracError("Invalid resubmit ID supplied - unable to load page correctly.", "Resubmit ID error")

        # if we are resubmitting a code review and we are the author or the manager
        if reviewID is not None and \
                (dbBack.getCodeReviewsByID(reviewID).Author == util.get_reporter_id(req) or
                 req.perm.has_permission('CODE_REVIEW_MGR')):
            review = dbBack.getCodeReviewsByID(reviewID)
            data['new'] = "no"
            data['oldid'] = reviewID
            # get code review data and populate
            userStructs = dbBack.getReviewers(reviewID)
            returnUsers = ""
            popUsers = []
            for struct in userStructs:
                returnUsers += struct.Reviewer + "#"
                popUsers.append(struct.Reviewer)

            rfiles = ReviewFile.select_by_review(self.env, reviewID)
            returnFiles = ""
            popFiles = []
            # Set up the file information
            for f in rfiles:
                returnFiles += "%s, %s, %s, %s#" % (f.path, f.version, f.start, f.end)
                tempFiles = []
                tempFiles.append(f.path)
                tempFiles.append(f.version)
                tempFiles.append(f.start)
                tempFiles.append(f.end)
                popFiles.append(tempFiles)

            data['name'] = review.Name
            data['notes'] = review.Notes
            data['reviewers'] = returnUsers
            data['prevUsers'] = popUsers
            data['prevFiles'] = popFiles

            # Figure out the users that were not included
            # in the previous code review so that they can be
            # added to the dropdown to select more users
            # (only check if all users were not included in previous code review)
            notUsers = []
            if len(popUsers) != len(allUsers): 
                for user in allUsers:
                    match = "no"
                    for candidate in popUsers:
                        if candidate == user:
                            match = "yes"
                            break
                    if match == "no":
                        notUsers.append(user)
                data['notPrevUsers'] = notUsers
                data['emptyList'] = 0
            else:
                data['notPrevUsers'] = []
                data['emptyList'] = 1

        #if we resubmitting a code review, and are neither the author and the manager
        elif reviewID is not None and \
                not dbBack.getCodeReviewsByID(reviewID).Author == util.get_reporter_id(req) and \
                not req.perm.has_permission('CODE_REVIEW_MGR'):
            TracError("You need to be a manager or the author of this code review to resubmit it.", "Access error")

        #if we are not resubmitting
        else:
            if req.args.get('reqAction') == 'createCodeReview':
                oldid = req.args.get('oldid')
                if oldid is not None:
                    review = dbBack.getCodeReviewsByID(oldid)
                    review.Status = "Closed"
                    review.save(db)
                returnid = self.createCodeReview(req)
                #If no errors then redirect to the viewCodeReview page
                req.redirect(self.env.href.peerReviewView() + '?Review=' + str(returnid))
            else:
                data['new'] = "yes"

        if data['new'] == "yes":
            data['reviewersSelectedValue'] = {'value': ''}
            data['filesSelectedValue'] = {'value': ''} 
        else:
            data['reviewersSelectedValue'] = {'value': returnUsers}
            data['filesSelectedValue'] = {'value': returnFiles} 

        data['users'] = allUsers
        data['cycle'] = itertools.cycle

        add_ctxt_nav_items(req)
        return 'peerReviewNew.html', data, None

    # Takes the information given when the page is posted
    # and creates a new code review struct in the database
    # and populates it with the information.  Also creates
    # new reviewer structs and file structs for the review.
    def createCodeReview(self, req):
        struct = CodeReviewStruct(None)
        struct.Author = util.get_reporter_id(req)
        struct.Status = 'Open for review'
        struct.DateCreate = int(time.time())
        struct.Name = req.args.get('Name')
        struct.Notes = req.args.get('Notes')
        id_ = struct.save(self.env.get_db_cnx())
        self.log.debug('BEN %s', id_)
        # loop here through all the reviewers
        # and create new reviewer structs based on them
        string = req.args.get('ReviewersSelected')
        tokens = string.split('#')
        for token in tokens:
            if token != "":
                struct = ReviewerStruct(None)
                struct.IDReview = id_
                struct.Reviewer = token
                struct.Status = 0
                struct.Vote = "-1"
                struct.save(self.env.get_db_cnx())

        # loop here through all included files
        # and create new file structs based on them
        files = req.args.get('FilesSelected')
        items = files.split('#')
        for item in items:
            if item != "":
                segment = item.split(',')
                rfile = ReviewFile(self.env)
                rfile.review_id = id_
                rfile.path = segment[0]
                rfile.version = segment[1]
                rfile.start = segment[2]
                rfile.end = segment[3]
                rfile.insert()
        return id_
