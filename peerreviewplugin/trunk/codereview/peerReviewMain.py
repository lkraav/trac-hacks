#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016 Cinc-th
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#
# Provides functionality for main page
# Works with peerReviewMain.html

import itertools

from trac.core import Component, implements
from trac.wiki.formatter import format_to_html
from trac.perm import IPermissionRequestor
from trac.resource import *
from trac.timeline.api import ITimelineEventProvider
from trac.util import Markup, format_date
from trac.util.datefmt import to_timestamp
from trac.util.text import _
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_ctxtnav
from trac.web.main import IRequestHandler
from genshi.builder import tag

from dbBackend import *
from model import Reviewer, PeerReviewModel, PeerReviewerModel


def add_ctxt_nav_items(req):
    add_ctxtnav(req, _("My Code Reviews"), "peerReviewMain", title=_("My Code Reviews"))
    add_ctxtnav(req, _("Create a Code Review"), "peerReviewNew", title=_("Create a Code review"))
    add_ctxtnav(req, _("Show files"), "peerreviewfile", title=_("Show reviewed files"))
    add_ctxtnav(req, _("Search Code Reviews"), "peerReviewSearch", _("Search Code Reviews"))


class PeerReviewMain(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
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

        data['allassigned'] = req.args.get('allassigned')
        data['allcreated'] = req.args.get('allcreated')

        r_tmpl = PeerReviewModel(self.env)
        r_tmpl.clear_props()
        if data['allcreated']:
            all_reviews = list(r_tmpl.list_matching_objects())
        else:
            all_reviews = [rev for rev in r_tmpl.list_matching_objects() if rev['status'] != "closed"]

        # fill the table of currently open reviews
        myreviews = []
        assigned_to_me =[]
        manager_reviews = []

        for rev in all_reviews:
            # Reviews created by me
            if rev['owner'] == req.authname:
                rev.date = format_date(rev['created'])
                myreviews.append(rev)

        r_tmpl = PeerReviewerModel(self.env)
        r_tmpl.clear_props()
        r_tmpl['reviewer'] = req.authname

        from peerReviewView import review_is_finished, review_is_locked
        if data['allassigned']:
            # Don't filter list here
            reviewer = list(r_tmpl.list_matching_objects())
        else:
            reviewer = [rev for rev in r_tmpl.list_matching_objects() if rev['status'] != "reviewed"]

        # All reviews assigned to me
        for item in reviewer:
            rev = PeerReviewModel(self.env, item['review_id'])
            if not review_is_finished(rev):
                #if not review_is_locked(rev) or data['allassigned']:
                rev.date = format_date(rev['created'])
                rev.reviewer = item
                assigned_to_me.append(rev)

        data['myreviews'] = myreviews
        data['manager_reviews'] = manager_reviews
        data['assigned_reviews'] = assigned_to_me
        data['cycle'] = itertools.cycle

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'hw/css/peerreview.css')
        add_ctxt_nav_items(req)

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
            add_stylesheet(req, 'hw/css/peerreview.css')

            for codeReview in codeReviewDetails:
                codereview_page = codereview_realm(id=codeReview.IDReview)
                reviewers = Reviewer.select_by_review_id(self.env, codeReview.IDReview)

                reviewersList = ''
                last = len(reviewers) - 1
                for idx, reviewer in enumerate(reviewers):
                    reviewersList = reviewersList + reviewer.reviewer
                    if idx != last:
                        reviewersList += ', '

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
            return tag('Assigned to: ', reviewersList,
                       tag.div(' Additional notes: '),
                       tag.div(
                           format_to_html(self.env, context, notes),
                           class_='notes'
                       ))

    # ITemplateProvider methods

    def get_templates_dirs(self):
        """Return the path of the directory containing the provided templates."""
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]