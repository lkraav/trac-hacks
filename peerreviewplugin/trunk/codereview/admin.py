# -*- coding: utf-8 -*-

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.web.chrome import add_warning

from dbBackend import dbBackend

__author__ = 'Cinc'


def calculate_review_status(env, newThreshold):
    # This function
    # Copyright (C) 2005-2006 Team5
    if newThreshold is not None:
        db = env.get_read_db()
        dbBack = dbBackend(db)

        dbBack.setThreshold(newThreshold)
        newThreshold = float(newThreshold)/100
        openArray = dbBack.getCodeReviewsByStatus("Open for review")
        for struct in openArray:
            voteyes = float(dbBack.getVotesByID("1", struct.IDReview))
            voteno = float(dbBack.getVotesByID("0", struct.IDReview))
            notvoted = float(dbBack.getVotesByID("-1", struct.IDReview))
            total_votes_possible = voteyes + voteno + notvoted
            if total_votes_possible != 0:
                vote_ratio = voteyes/total_votes_possible
            else:
                vote_ratio = 0
            # calculate vote ratio, while preventing divide by zero tests
            if vote_ratio >= newThreshold:
                struct.Status = "Reviewed"
                struct.save(db)
        reviewArray = dbBack.getCodeReviewsByStatus("Reviewed")
        for struct in reviewArray:
            voteyes = float(dbBack.getVotesByID("1", struct.IDReview))
            voteno = float(dbBack.getVotesByID("0", struct.IDReview))
            notvoted = float(dbBack.getVotesByID("-1", struct.IDReview))
            total_votes_possible = voteyes + voteno + notvoted
            if total_votes_possible != 0:
                vote_ratio = voteyes/total_votes_possible
            else:
                vote_ratio = 0
            # calculate vote ratio, while preventing divide by zero tests
            if vote_ratio < newThreshold:
                struct.Status = "Open for review"
                struct.save(db)


class MgrOptionsAdminPlugin(Component):
    """Set threshold percentage"""
    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'CODE_REVIEW_MGR' in req.perm:
            yield ('codereview', 'Code review', 'threshold', 'Threshold')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('CODE_REVIEW_MGR')

        db = self.env.get_read_db()
        dbBack = dbBackend(db)

        if req.method=='POST':
            percentage = req.args.get('percentage', '')
            if not percentage:
                add_warning(req, u"You must specify a  percentage between 0 and 100.")
                req.redirect(req.href.admin(cat, page))
            elif int(percentage) < 0 or int(percentage) > 100:
                add_warning(req, u"You must specify a  percentage between 0 and 100.")
                req.redirect(req.href.admin(cat, page))
            else:
                calculate_review_status(self.env, percentage)
                req.redirect(req.href.admin(cat, page))

        data = {'percentage': dbBack.getThreshold()}

        return 'admin_mgr_options.html', data