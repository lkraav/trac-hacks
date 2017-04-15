# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Radek Bartoň <blackhex@post.cz>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac.core import Component, implements
from trac.web.main import IRequestHandler
from trac.web.chrome import web_context

from tracdiscussion.api import DiscussionApi


class DiscussionAjax(Component):
    """[main] Implements the AJAX requests handler."""

    implements(IRequestHandler)

    # IRequestHandler methods

    def match_request(self, req):
        # Try to match request pattern to request URL.
        match = re.match(
            r'/discussion/ajax(?:/(forum|topic|message)/(\d+)(?:/?$))',
            req.path_info)
        if match:
            resource_type = match.group(1)
            resource_id = match.group(2)
            if resource_type == 'forum':
                req.args['forum'] = resource_id
            if resource_type == 'topic':
                req.args['topic'] = resource_id
            if resource_type == 'message':
                req.args['message'] = resource_id
        return match

    def process_request(self, req):
        # Create request context.
        context = web_context(req)
        context.realm = 'discussion-ajax'

        # Process request and return content.
        api = DiscussionApi(self.env)
        template, data = api.process_discussion(context)

        return template, data, None
