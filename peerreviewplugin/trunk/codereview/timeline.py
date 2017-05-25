#
# Copyright (C) 2005-2006 Team5
# Copyright (C) 2016 Cinc-th
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#

from trac.core import Component, implements
from trac.wiki.formatter import format_to_html
from trac.resource import Resource
from trac.timeline.api import ITimelineEventProvider
from trac.util.datefmt import to_timestamp
from trac.util.html import html as tag
from trac.util.translation import _
from trac.web.chrome import add_stylesheet

from model import PeerReviewModel, PeerReviewerModel


class PeerReviewTimeline(Component):
    implements(ITimelineEventProvider)

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('peerreview', _('Code Reviews'))

    def get_timeline_events(self, req, start, stop, filters):
        if 'peerreview' in filters:
            codereview_realm = Resource('peerreview')

            reviews = PeerReviewModel.reviews_by_period(self.env, to_timestamp(start), to_timestamp(stop))

            add_stylesheet(req, 'hw/css/peerreview.css')

            for codereview in reviews:
                codereview_page = codereview_realm(id=codereview['review_id'])
                rm = PeerReviewerModel(self.env)
                rm.clear_props()
                rm['review_id'] = codereview['review_id']
                reviewers = list(rm.list_matching_objects())

                reviewers_list = ''
                last = len(reviewers) - 1
                for idx, reviewer in enumerate(reviewers):
                    reviewers_list = reviewers_list + reviewer['reviewer']
                    if idx != last:
                        reviewers_list += ', '

                yield('peerreview', codereview['created'], codereview['owner'],
                      (codereview_page, codereview['name'], codereview['notes'],
                       reviewers_list))

    def render_timeline_event(self, context, field, event):
        codereview_page, name, notes, reviewersList = event[3]

        if field == 'url':
            return context.href.peerReviewView(Review=codereview_page.id)
        if field == 'title':
            return tag(_('Code review '), tag.em(name), _(' has been raised'))
        if field == 'description':
            return tag(_('Assigned to: '), reviewersList,
                       tag.div(_('Additional notes:')),
                       tag.div(
                           format_to_html(self.env, context, notes),
                           class_='notes'
                       ))
