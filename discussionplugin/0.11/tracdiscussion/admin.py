# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2010 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import time

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.mimeview import Context
from trac.perm import IPermissionRequestor

from tracdiscussion.api import DiscussionApi


class DiscussionWebAdmin(Component):
    """[opt] Implements discussion plugin administration method access
       via web-UI.
    """

    implements(IAdminPanelProvider)

    # IAdminPageProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('DISCUSSION_ADMIN'):
            yield ('discussion', 'Discussion System', 'forum', 'Forums')
            yield ('discussion', 'Discussion System', 'group', 'Forum Groups')

    def render_admin_panel(self, req, category, page, path_info):
        if page == 'forum':
            if not req.args.has_key('group'):
                req.args['group'] = '-1'
            if path_info:
                req.args['forum'] = path_info
        else:
            if path_info:
                req.args['group'] = path_info

        # Create context with additional arguments prepared before.
        context = Context.from_request(req)
        context.realm = 'discussion-admin'

        # Process admin panel request.
        api = DiscussionApi(self.env)
        template, data = api.process_discussion(context)

        if context.redirect_url:
            # Redirect request if needed.
            href = req.href(context.redirect_url[0]) + context.redirect_url[1]
            self.log.debug("Redirecting to %s" % href)
            req.redirect(req.href('discussion', 'redirect',
                                  redirect_url=href))
        else:
            return template, data
