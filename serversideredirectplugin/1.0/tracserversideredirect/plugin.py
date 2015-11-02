# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 Martin Scharrer <martin@scharrer-online.de>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re

from genshi.builder import tag
from trac.core import *
from trac.util.text import stripws
from trac.util.translation import _, tag_
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import web_context
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import concat_path_query_fragment
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

from tracextracturl.extracturl import extract_url

MACRO = re.compile(r'.*\[\[[rR]edirect\((.*)\)\]\]')


class ServerSideRedirectPlugin(Component):
    """This Trac plug-in implements a server sided redirect functionality.
The user interface is the wiki macro `Redirect` (alternatively `redirect`).

== Description ==
Website: https://trac-hacks.org/wiki/ServerSideRedirectPlugin

This plug-in allow to place a redirect macro at the start of any wiki
page which will cause an server side redirect when the wiki page is
viewed.

This plug-in is compatible (i.e. can be used) with the client side
redirect macro TracRedirect but doesn't depend on it. Because the
redirect is caused by the server (using a HTTP redirect request to the
browser) it is much faster and less noticeable for the user. The
back-link feature of TracRedirect can also be used for server side
redirected pages because both generate the same URL attributes.

To edit a redirecting wiki page access its URL with `?action=edit`
appended. To view the page either use `?action=view`, which will print
the redirect target (if TracRedirect isn't active, which will redirect
the wiki using client side code), or `?redirect=no` which disables
redirection of both the ServerSideRedirectPlugin and TracRedirect
plug-in.

Direct after the redirect target is added (or modified) Trac will
automatically reload it, as it does with all wiki pages. This plug-in
will detect this and not redirect but display the wiki page with the
redirect target URL printed to provide feedback about the successful
change. However, further visits will trigger the redirect.

== Usage Examples ==
The following 'macro' at the begin of the wiki page will cause a
redirect to the ''!OtherWikiPage''.
{{{
[[redirect(OtherWikiPage)]]
[[Redirect(OtherWikiPage)]]
}}}
Any other [TracLinks TracLink] can be used:
{{{
[[redirect(wiki:OtherWikiPage)]]
[[Redirect(wiki:OtherWikiPage)]]
[[redirect(source:/trunk/file.py)]]
[[Redirect(source:/trunk/file.py)]]
[[redirect(http://www.example.com/)]]
[[Redirect(http://www.example.com/)]]
}}}
    """
    implements(IRequestHandler, IRequestFilter, IWikiMacroProvider)

    def expand_macro(self, formatter, name, content):
        """Print redirect notice after edit."""

        content = stripws(content)
        target = extract_url(self.env, formatter.context, content)
        if not target:
            target = formatter.req.href.wiki(content)

        return tag.div(
            tag.strong('This page redirects to: '),
            tag.a(content, href=target),
            class_='system-message',
            id='notice'
        )

    def get_macros(self):
        """Provide but do not redefine the 'redirect' macro."""
        get = self.env.config.get
        if get('components', 'redirect.*') == 'enabled' or \
                get('components', 'redirect.redirect.*') == 'enabled' or \
                get('components',
                    'redirect.redirect.tracredirect') == 'enabled':
            return ['Redirect']
        else:
            return ['redirect', 'Redirect']

    def get_macro_description(self, name):
        if name == 'Redirect':
            return self.__doc__
        else:
            return "See macro `Redirect`."

    # IRequestHandler methods

    def match_request(self, req):
        """Only handle request when selected from `pre_process_request`."""
        return False

    def process_request(self, req):
        """Redirect to pre-selected target."""
        target = req.args.get('redirect-target')
        if target:
            # Check for self-redirect:
            if target and target == req.href(req.path_info):
                change = tag.a(_("change"), href=target + "?action=edit")
                message = tag_("Please %(change)s the redirect target to "
                               "another page.", change=change)
                data = {
                    'title': "Page redirects to itself!",
                    'message': message,
                    'type': 'TracError'
                }
                req.send_error(data['title'], status=409,
                               env=self.env, data=data)

            # Check for redirect pair, i.e. A->B, B->A
            redirected_from = req.args.get('redirectedfrom', '')
            if target and target == req.href.wiki(redirected_from):
                this = tag.a(_("this"),
                             href=req.href(req.path_info, action="edit"))
                redirecting = tag.a(_("redirecting"),
                                    href=target + "?action=edit")
                message = tag_("Please change the redirect target on "
                               "%(this)s page or the %(redirecting)s page.",
                               this=this, redirecting=redirecting)
                data = {
                    'title': "Redirect target redirects back to this page!",
                    'message': message,
                    'type': 'TracError'
                }
                req.send_error(data['title'], status=409,
                               env=self.env, data=data)

            # Add back link information for internal links:
            if target and target[0] == '/':
                redirectfrom = "redirectedfrom=" + req.path_info[6:]
                target = concat_path_query_fragment(target, redirectfrom)
            req.redirect(target)
        raise TracError("Invalid redirect target!")

    def _get_redirect(self, req):
        """Checks if the request should be redirected."""
        if req.path_info in ('/', '/wiki'):
            wiki = 'WikiStart'
        elif not req.path_info.startswith('/wiki/'):
            return None
        else:
            wiki = req.path_info[6:]

        wp = WikiPage(self.env, wiki, req.args.get('version'))

        if not wp.exists:
            return None

        # Check for redirect "macro":
        m = MACRO.match(wp.text)
        if not m:
            return None
        wikitarget = stripws(m.group(1))
        ctxt = web_context(req)
        redirect_target = extract_url(self.env, ctxt, wikitarget)
        if not redirect_target:
            redirect_target = req.href.wiki(wikitarget)
        return redirect_target

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if not isinstance(handler, WikiModule):
            return handler

        args = req.args
        if not req.path_info.startswith('/wiki/') and \
                not req.path_info == '/wiki' and not req.path_info == '/':
            self.log.debug("SSR: no redirect: Path is not a wiki path")
            return handler
        if req.method != 'GET':
            self.log.debug("SSR: no redirect: No GET request")
            return handler
        if 'action' in args:
            self.log.debug("SSR: no redirect: action=" + args['action'])
            return handler
        if 'version' in args:
            self.log.debug("SSR: no redirect: version=...")
            return handler
        if 'redirect' in args and args['redirect'].lower() == 'no':
            self.log.debug("SSR: no redirect: redirect=no")
            return handler
        if req.environ.get('HTTP_REFERER', '').find('action=edit') != -1:
            self.log.debug("SSR: no redirect: HTTP_REFERER includes "
                           "action=edit")
            return handler
        target = self._get_redirect(req)
        if target:
            self.log.debug("SSR: redirect!")
            req.args['redirect-target'] = target
            return self
        self.log.debug("SSR: no redirect: No redirect macro found.")
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
