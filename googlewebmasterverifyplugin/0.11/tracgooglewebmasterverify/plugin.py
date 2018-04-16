# -*- coding: utf-8 -*-
"""
 Google Webmaster Verify Plugin for Trac
 Copyright (c) March 2009  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.
"""

from trac.config import ListOption
from trac.core import Component, implements
from trac.web.api import IRequestHandler, RequestDone
from trac.web.chrome import add_meta


class GoogleWebmasterVerifyPlugin(Component):
    """Simply plugin to return verify webpages for Google Webmaster Service.
    """

    implements(IRequestHandler)

    vlist = ListOption('googlewebmasterverify', 'verify',
                       doc="Verification code(s)")

    # IRequestHandler methods

    def match_request(self, req):
        """Check if requested URL is '/googleXX..XX.html' where XX..XX is in
        config list."""
        try:
            path = req.path_info
            if path.startswith("/google") and path.endswith(".html"):
                path = path[7:-5]
            else:
                return False

            if path in self.vlist:
                return True
            else:
                return False
        except:
            return False

    def process_request(self, req):
        """Send an empty HTTP 200 OK response."""
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        req.write("google-site-verification: " + req.path_info[1:])
        raise RequestDone

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if self.mvlist:
            for code in self.mvlist:
                self.env.log.debug("add_meta: " + code)
                add_meta(req, code, name="google-site-verification")
        return template, data, content_type
