# -*- coding: utf-8 -*-

import re

from trac.core import *
from trac.mimeview import Context
from trac.config import Option
from trac.util.html import html
from trac.resource import Resource

from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler

from tracdiscussion.api import *

class DiscussionCore(Component):
    """
        The core module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # Configuration options.
    title = Option('discussion', 'title', 'Discussion',
      'Main navigation bar button title.')

    # ITemplateProvider methods.

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('discussion', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods.

    def get_active_navigation_item(self, req):
        return 'discussion'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DISCUSSION_VIEW'):
            yield 'mainnav', 'discussion', html.a(self.title,
              href = req.href.discussion())

    # IRequestHandler methods.

    def match_request(self, req):
        if req.path_info == '/discussion/redirect':
            # Proces redirection request.
            req.redirect(req.args.get('redirect_url'))
        else:
            # Prepare regular requests.
            match = re.match(r'''/discussion(?:/?$|/(forum|topic|message)/(\d+)(?:/?$))''',
              req.path_info)
            if match:
                resource_type = match.group(1)
                resource_id = match.group(2)
                if resource_type == 'forum':
                    req.args['forum'] = resource_id
                if resource_type == 'topic':
                    req.args['topic'] = resource_id
                if resource_type== 'message':
                    req.args['message'] = resource_id
            return match

    def process_request(self, req):
        # Create request context.
        context = Context.from_request(req)
        context.realm = 'discussion-core'
        if req.args.has_key('forum'):
            context.resource = Resource('discussion', 'forum/%s' % (
              req.args['forum'],))
        if req.args.has_key('topic'):
            context.resource = Resource('discussion', 'topic/%s' % (
              req.args['topic'],))
        if req.args.has_key('message'):
            context.resource = Resource('discussion', 'message/%s' % (
              req.args['message'],))

        # Process request and return content.
        api = self.env[DiscussionApi]
        template, data = api.process_discussion(context)

        if context.redirect_url:
            # Redirect if needed.
            href = req.href(context.redirect_url[0]) + context.redirect_url[1]
            self.log.debug("Redirecting to %s" % (href))
            req.redirect(req.href('discussion', 'redirect', redirect_url =
              href))
        else:
            # Return template and its data.
            return template, data, None
