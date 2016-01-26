#
# Copyright (C) 2005-2006 Team5
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#

# Provides functionality for main page
# Works with peerReviewMain.cs

import itertools

from genshi.builder import tag

from trac import util
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.resource import *
from trac.timeline.api import ITimelineEventProvider
from trac.util import Markup
from trac.util.datefmt import to_timestamp
from trac.web.chrome import INavigationContributor, add_stylesheet
from trac.web.main import IRequestHandler

from dbBackend import *
from model import Review

class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler,
               IPermissionRequestor, ITimelineEventProvider)
        
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'peerReviewMain'
                
    def get_navigation_items(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('mainnav', 'peerReviewMain',
                   Markup('<a href="%s">Peer Review</a>') % req.href.peerReviewMain())

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['CODE_REVIEW_DEV', ('CODE_REVIEW_MGR', ['CODE_REVIEW_DEV'])]

    # IRequestHandler methods
    def match_request(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            return req.path_info == '/peerReviewMain'
        return False

    def process_request(self, req):
        req.perm.require('CODE_REVIEW_DEV')

        data = {}
        # test whether this user is a manager or not
        if 'CODE_REVIEW_MGR' in req.perm:
            data['manager'] = True
        else:
            data['manager'] = False

        db = self.env.get_read_db()
        dbBack = dbBackend(db)

        all_reviews = [rev for rev in Review.select(self.env) if rev.status != "Closed"]
        rev_by_reviewer = [rev for rev in Review.select_by_reviewer(self.env, req.authname) if rev.status != "Closed"]

        # fill the table of currently open reviews
        myreviews = []
        assigned_to_me =[]
        manager_reviews = []
        for rev in all_reviews:
            # Reviews created by me
            if rev.author == req.authname:
                myreviews.append(rev)
            # Reviews a manager must handle
            if rev.status == "Ready for inclusion":
                manager_reviews.append(rev)

        # All reviews assigned to me
        for rev in rev_by_reviewer:
            if rev.status != "Ready for inclusion":
                reviewstruct = dbBack.getReviewerEntry(rev.review_id,req.authname)
                if reviewstruct.Vote == -1:
                    rev.vote = 'Not voted'
                elif reviewstruct.Vote == 0:
                    rev.vote = 'Rejected'
                elif reviewstruct.Vote == 1:
                    rev.vote = 'Accepted'
                assigned_to_me.append(rev)

        data['myreviews'] = myreviews
        data['manager_reviews'] = manager_reviews
        data['assigned_reviews'] = assigned_to_me
        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')   

        return 'peerReviewMain.html', data, None

    # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('codereview', 'Code Reviews')

    def get_timeline_events(self, req, start, stop, filters):
        if 'codereview' in filters:
            codereview_realm = Resource('codereview')

            db = self.env.get_db_cnx()
            dbBack = dbBackend(db)
            codeReviewDetails = dbBack.getCodeReviewsInPeriod(to_timestamp(start), to_timestamp(stop))

            for codeReview in codeReviewDetails:
                codereview_page = codereview_realm(id=codeReview.IDReview)
                reviewers = dbBack.getReviewers(codeReview.IDReview)

                reviewersList = ''
                for reviewer in reviewers:
                    reviewersList = reviewersList + reviewer.Reviewer + ','
           
                yield('codereview', codeReview.DateCreate, codeReview.Author,
                      (codereview_page, codeReview.Name, codeReview.Notes,
                       reviewersList))

    def render_timeline_event(self, context, field, event):
        codereview_page, name, notes, reviewersList = event[3]

        if field == 'url':
            return context.href.peerReviewView(Review=codereview_page.id)
        if field == 'title':
            return tag('Code review ', tag.em(name), ' has been raised')
        if field == 'description':
            return tag('Assigned to: ', reviewersList, tag.br(), ' Additional notes: ', notes)
