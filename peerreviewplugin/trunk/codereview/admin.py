# -*- coding: utf-8 -*-

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.web.chrome import add_warning

from dbBackend import dbBackend
from model import Review, Vote

__author__ = 'Cinc'


def calculate_review_status(env, newThreshold):
    def calc_vote_ratio(r):
        votes = Vote(env, r.review_id)
        voteyes = float(votes.yes)
        voteno = float(votes.no)
        notvoted = float(votes.pending)
        total_votes_possible = voteyes + voteno + notvoted
        if total_votes_possible != 0:
            vote_ratio = voteyes/total_votes_possible
        else:
            vote_ratio = 0
        return vote_ratio

    if newThreshold is not None:
        db = env.get_read_db()
        dbBack = dbBackend(db)

        dbBack.setThreshold(newThreshold)
        newThreshold = float(newThreshold)/100

        all_reviews = Review.select(env)

        open_reviews = [rev for rev in all_reviews if rev.status == "Open for review"]
        for r in open_reviews:
            # calculate vote ratio, while preventing divide by zero tests
            if calc_vote_ratio(r) >= newThreshold:
                r.status = "Reviewed"
                r.update()

        rev_reviews = [rev for rev in all_reviews if rev.status == "Reviewed"]
        for r in rev_reviews:
            # calculate vote ratio, while preventing divide by zero tests
            if calc_vote_ratio(r) < newThreshold:
                r.status = "Open for review"
                r.update()


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