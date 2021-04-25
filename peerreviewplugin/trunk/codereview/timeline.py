# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#
from .model import PeerReviewModel, PeerReviewerModel, ReviewFileModel
from trac.core import Component, implements
from trac.wiki.formatter import format_to_html
from trac.resource import Resource, get_resource_url
from trac.timeline.api import ITimelineEventProvider
from trac.util.datefmt import from_utimestamp, to_utimestamp
from trac.util.html import html as tag
from trac.util.translation import _
from trac.web.chrome import add_stylesheet


class PeerReviewTimeline(Component):
    """Provide code review events for the timeline.

    [[BR]]
    You need permission {{{CODE_REVIEW_VIEW}}} to see code review events.

    '''Note:''' It is safe to disable this plugin when no timeline for code reviews should be shown.
    """

    implements(ITimelineEventProvider)

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if 'CODE_REVIEW_VIEW' in req.perm:
            yield ('peerreview', _('Code Reviews'))

    def get_timeline_events(self, req, start, stop, filters):
        if 'peerreview' in filters:
            ts_start = to_utimestamp(start)
            ts_stop = to_utimestamp(stop)

            coderev_resource = Resource('peerreview')

            add_stylesheet(req, 'hw/css/peerreview.css')

            def reviewers_for_review(rev_id):
                rm = PeerReviewerModel(self.env)
                rm.clear_props()
                rm['review_id'] = rev_id
                reviewers_lst = list(rm.list_matching_objects())

                rev_list = ''
                last = len(reviewers_lst) - 1
                for idx, reviewer in enumerate(reviewers_lst):
                    rev_list = rev_list + reviewer['reviewer']
                    if idx != last:
                        rev_list += ', '
                return rev_list

            def get_files_for_review_id(review_id):
                """Get all files belonging to the given review id. Provide the number of comments if asked for."""
                rfm = ReviewFileModel(self.env)
                rfm.clear_props()
                rfm['review_id'] = review_id
                rev_files = list(rfm.list_matching_objects())
                return rev_files

            with self.env.db_query as db:
                reviews = {}
                for rid, t, author, field, oldvalue, newvalue \
                        in db("""
                                        SELECT pc.review_id, pc.time, pc.author,
                                               pc.field, pc.oldvalue, pc.newvalue
                                        FROM peerreview_change AS pc
                                        WHERE pc.time>=%s AND pc.time<=%s
                                        ORDER BY pc.time, pc.review_id
                                        """, (ts_start, ts_stop)):
                    if not (oldvalue or newvalue):
                        # ignore empty change corresponding to custom field
                        # created (None -> '') or deleted ('' -> None)
                        continue
                    if field == 'status':
                        try:
                            codereview, reviewers_list, coderev_page, files = reviews[rid]
                        except KeyError:
                            reviews[rid] = [PeerReviewModel(self.env, rid),
                                            reviewers_for_review(rid),
                                            coderev_resource(id=rid),
                                            get_files_for_review_id(rid)
                                            ]
                            codereview, reviewers_list, coderev_page, files = reviews[rid]
                        yield('peerreview', from_utimestamp(t), codereview['owner'],
                              (coderev_page, codereview['name'], codereview['notes'],
                               reviewers_list, oldvalue, newvalue, files))


    def render_timeline_event(self, context, field, event):
        codereview_page, name, notes, reviewersList, oldstatus, newstatus, files = event[3]

        if field == 'url':
            return get_resource_url(self.env, codereview_page, context.href)
        if field == 'title':
            return tag(_('Code review '), tag.em(name), " (%s)" % codereview_page.id,
                       _(": Status changed from '%s' to '%s'" % (oldstatus, newstatus))
                       )

        def filelist():
            ul = tag.ul()
            for f in files:
                ul.append(tag.li(
                                 tag.a('%s @ %s' % (f['path'], f['changerevision']),
                                       href='peerreviewperform?IDFile=%s' % f['file_id']
                                       )
                                )
                          )
            return ul

        if field == 'description':
            return tag(_('Assigned to: '), tag.em(reviewersList),
                       tag.div(_('Additional notes:')),
                       tag.div(
                           format_to_html(self.env, context, notes),
                           class_='notes'
                       ),
                       tag.div(_('Files:')),
                       filelist()
                       )
