# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#

from trac.core import Component, implements
from trac.web.chrome import INavigationContributor, add_stylesheet
from trac.web.main import IRequestHandler
from .peerReviewMain import add_ctxt_nav_items


__author__ = 'Cinc'
__license__ = "BSD"


class PeerReviewReport(Component):
    """Show a page with reports for getting data from code reviews.

    [[BR]]
    Code review reports are normal Trac SQL reports. A report will be shown on the code review report page when the
    report description starts with the following comment:

    {{{
    {{{
    #!comment
    codereview=1
    }}}
    }}}
    """
    implements(INavigationContributor, IRequestHandler)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'peerReviewMain'

    def get_navigation_items(self, req):
        return

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/peerreviewreport'

    def process_request(self, req):
        def is_codereview_report(desc):
            """Check if wiki comment section holds 'codereview = 1' as first line."""
            lst = desc.splitlines()
            if '{{{' not in lst or '}}}' not in lst or '#!comment' not in lst:
                return False
            lst = lst[lst.index('#!comment')+1:lst.index('}}}')]  # contents of comment section
            if ''.join(lst[0].split()) == 'codereview=1':
                return True
            return False

        req.perm.require('CODE_REVIEW_DEV')

        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, title, description FROM report")
        reports = []
        for row in cursor:
            if is_codereview_report(row[2]):
                reports.append({
                    'id': row[0],
                    'title': row[1],
                    'desc': row[2]
                })

        data = {
            'reports': reports
        }

        add_stylesheet(req, 'common/css/report.css')

        add_ctxt_nav_items(req)
        return 'peerreview_report.html', data, None
