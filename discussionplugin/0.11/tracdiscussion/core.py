# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2006-2011 Radek Bartoň <blackhex@post.cz>
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.config import Option
from trac.mimeview.api import Context, IContentConverter, Mimeview
from trac.resource import Resource, get_resource_url
from trac.util.html import html
from trac.util.translation import _, N_
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_link
from trac.web.main import IRequestHandler

from tracdiscussion.api import DiscussionApi


class DiscussionCore(Component):
    """[main] Provides a message board including wiki links to discussions,
    topics and messages.
    """

    implements(IContentConverter, INavigationContributor,
               IRequestHandler, ITemplateProvider)

    title = Option('discussion', 'title', N_('Discussion'),
                   doc=_('Main navigation bar button title.'))

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('discussion', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'discussion'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DISCUSSION_VIEW'):
            yield 'mainnav', 'discussion', html.a(_(self.title),
                                                  href=req.href.discussion())

    # IContentConverter methods

    def get_supported_conversions(self):
        yield ('rss', _('RSS Feed'), 'xml', 'tracdiscussion.topic',
          'application/rss+xml', 8)
        yield ('rss', _('RSS Feed'), 'xml', 'tracdiscussion.forum',
          'application/rss+xml', 5)

    def convert_content(self, req, mimetype, resource, key):
        if key == 'rss':
            return self._export_rss(req, resource)

    # IRequestHandler methods.

    def match_request(self, req):
        if req.path_info == '/discussion/redirect':
            # Process redirection request.
            req.redirect(req.args.get('redirect_url'))
        else:
            # Try to match request pattern to request URL.
            match = re.match(
                r'''/discussion(?:/?$|/(forum|topic|message)/(\d+)(?:/?$))''',
                req.path_info
                )
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

        # Redirect to content converter if requested.
        if req.args.has_key('format'):
            format = req.args.get('format')
            if req.args.has_key('topic'):
                in_type = 'tracdiscussion.topic'
                Mimeview(self.env).send_converted(
                    req, in_type, context.resource, format, filename=None)
            elif req.args.has_key('forum'):
                in_type = 'tracdiscussion.forum'
                Mimeview(self.env).send_converted(
                    req, in_type, context.resource, format, filename=None),

        api = DiscussionApi(self.env)
        template, data = api.process_discussion(context)

        if context.redirect_url:
            # Redirect, if needed.
            href = req.href(context.redirect_url[0]) + context.redirect_url[1]
            self.log.debug(_("Redirecting to %s") % href)
            req.redirect(req.href('discussion', 'redirect',
                                  redirect_url=href))
        else:
            # Add links to other formats.
            if context.forum or context.topic or context.message:
                for conversion in Mimeview(self.env) \
                        .get_supported_conversions('tracdiscussion.topic'):
                    format, name, extension, in_mimetype, out_mimetype, \
                        quality, component = conversion
                    conversion_href = get_resource_url(self.env,
                                                       context.resource,
                                                       context.req.href,
                                                       format=format)
                    add_link(context.req, 'alternate', conversion_href, name,
                             out_mimetype, format)
            return template, data, None

    # Internal methods

    def _export_rss(self, req, resource):
        # Create request context.
        context = Context.from_request(req)
        context.realm = 'discussion-core'
        context.resource = resource

        # Process request and get template and template data.
        api = DiscussionApi(self.env)
        template, data = api.process_discussion(context)
        output = Chrome(self.env).render_template(req, template, data,
                                                  'application/rss+xml')
        return output, 'application/rss+xml'
