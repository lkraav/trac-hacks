#
# Copyright (C) 2016 Cinc-th
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Team5
#
# Provides functionality for file list page

import itertools

from trac.core import Component, implements
from trac.util.text import _, CRLF
from trac.util import http_date
from trac.util.presentation import Paginator
from trac.web.chrome import INavigationContributor, add_stylesheet, add_link
from trac.web.main import IRequestHandler, RequestDone

from peerReviewMain import add_ctxt_nav_items
from model import ReviewFileModel


class PeerReviewFile(Component):
    implements(INavigationContributor, IRequestHandler)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return

    # IRequestHandler methods

    def match_request(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            return req.path_info == '/peerreviewfile'
        return False

    def process_request(self, req):
        req.perm.require('CODE_REVIEW_DEV')

        num_page = int(req.args.get('max', 20))  # items per page to show
        page_href = req.href.peerreviewfile
        cur_page = int(req.args.get('page', 1))
        # For paginating
        start = num_page * (cur_page - 1)
        end = num_page * cur_page

        rfm = ReviewFileModel(self.env)
        rfm.clear_props()
        rev_files = list(rfm.list_matching_objects())

        format = req.args.get('format')
        if format in ('cvs', 'txt'):
            self.send_cvs_data(req, rev_files)  # This ends the request

        # Prepare the Paginator
        results = Paginator(rev_files[start:end], cur_page-1, max_per_page=num_page, num_items=len(rev_files))
        results.show_index = True
        if req:
            if results.has_next_page:
                next_href = page_href(max=num_page, page=cur_page + 1)
                add_link(req, 'next', next_href, _('Next Page'))

            if results.has_previous_page:
                prev_href = page_href(max=num_page, page=cur_page - 1)
                add_link(req, 'prev', prev_href, _('Previous Page'))
        else:
            results.show_index = False

        pagedata = []
        shown_pages = results.get_shown_pages(21)
        for page in shown_pages:
            pagedata.append([req.href.peerreviewfile(max=num_page, page=page), None,
                             str(page), _('Page %(num)d', num=page)])

        results.shown_pages = [dict(zip(['href', 'class', 'string', 'title'],
                                        p)) for p in pagedata]
        results.current_page = {'href': None, 'class': 'current',
                                'string': str(results.page + 1),
                                'title':None}
        # Paginator end
        data = {'review_files': rev_files[start:end],
                'item_page': num_page,
                'paginator': results,
                'cycle': itertools.cycle}

        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'common/css/browser.css')
        add_ctxt_nav_items(req)
        add_link(req, 'alternate', req.href.peerreviewfile(format='cvs'), 'Comma-delimited Text (CVS)',
                 'text/csv')

        return 'peerreviewfile.html', data, None

    def send_cvs_data(self, req, rev_files):

        cvs_data = u""
        for item in rev_files:
            if cvs_data:
                cvs_data += CRLF
            cvs_data += "%s,%s,%s,%s,%s,%s,%s,%s,%s" % (item['file_id'], item['path'], item['review_id'],
                                                     item['changerevision'], item['revision'],
                                                     item['line_start'], item['line_end'],
                                                     item['hash'], item['status'])
        send_data = cvs_data.encode('utf-8')
        req.send_response(200)
        req.send_header('Content-Type', 'text/csv; charset=utf-8')

        req.send_header('Content-Length', len(send_data))
        req.send_header('Last-Modified', http_date())
        req.end_headers()
        req.write(send_data)
        raise RequestDone
