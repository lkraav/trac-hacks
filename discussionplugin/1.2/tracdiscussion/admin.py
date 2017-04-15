# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2010 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.web.chrome import web_context

from tracdiscussion.api import DiscussionApi


class DiscussionWebAdmin(Component):
    """[opt] Implements discussion plugin administration method access
       via web-UI.
    """

    implements(IAdminPanelProvider)

    # IAdminPageProvider methods

    def get_admin_panels(self, req):
        if 'DISCUSSION_ADMIN' in req.perm:
            yield 'discussion', 'Discussion System', 'forum', 'Forums'
            yield 'discussion', 'Discussion System', 'group', 'Forum Groups'

    def render_admin_panel(self, req, category, page, path_info):
        if page == 'forum':
            if 'group' not in req.args:
                req.args['group'] = '-1'
            if path_info:
                req.args['forum'] = path_info
        else:
            if path_info:
                req.args['group'] = path_info

        # Create context with additional arguments prepared before.
        context = web_context(req)
        context.realm = 'discussion-admin'

        # Process admin panel request.
        api = DiscussionApi(self.env)
        template, data = api.process_discussion(context)

        if context.redirect_url:
            # Redirect request if needed.
            href = req.href(context.redirect_url[0]) + context.redirect_url[1]
            self.log.debug("Redirecting to %s", href)
            req.redirect(req.href('discussion', 'redirect',
                                  redirect_url=href))
        else:
            return template, data
