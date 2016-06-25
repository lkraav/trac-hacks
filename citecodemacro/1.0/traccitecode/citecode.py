# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
import urlparse
import mimetypes
import os

from genshi.core import escape
from trac.core import Component, implements
from trac.mimeview import Mimeview, Context
from trac.mimeview.api import is_binary
from trac.web.chrome import add_script, add_script_data, ITemplateProvider, Chrome
from trac.web.main import IRequestFilter, IRequestHandler
from trac.wiki.macros import WikiMacroBase
from trac.versioncontrol import RepositoryManager

class CiteCodeMacro(WikiMacroBase):
    def __init__(self):
        self.repoman = RepositoryManager(self.env)
        self.mimeview = Mimeview(self.env)

    def expand_macro(self, formatter, name, content):
        self.log.debug("content=%s" % content)
        # parse the argument
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(content)
        self.log.debug("scheme=%s, netloc=%s, path=%s, params=%s, query=%s, fragment=%s"
                % (scheme, netloc, path, params, query, fragment))
        qs = urlparse.parse_qs(query)
        self.log.debug("qs=%s" % qs)

        reponame, repo, path = self.repoman.get_repository_by_path(path)
        try:
            if 'rev' in qs:
                rev = qs['rev'][0].encode()
            else:
                rev = None
            self.log.debug("rev=%s" % rev)
            node = repo.get_node(path, rev = rev)
            content = node.get_content()
            if content == None:
                self.log.debug("node is directory")
                return "<p>%s</p>" % escape(content)
            else:
                context = Context.from_request(formatter.req)
                content_type = node.get_content_type() or mimetypes.guess_type(path)[0]
                self.log.debug("content_type=%s" % str(content_type))
                content = content.read()
                if fragment != "" and not is_binary(content):
                    m = re.match("L(\d+)(-L?(\d+))?", fragment)
                    if m != None:
                        start, _, end = m.groups()
                        end = end or start
                        lines = content.splitlines()[int(start)-1:int(end)]
                        content = "\n".join(lines)
                xhtml = self.mimeview.render(
                        context = context,
                        mimetype = content_type,
                        content = content,
                        filename = "")
                return xhtml
        finally:
            repo.close()

class CiteCodeAndCreateTicket(Chrome):
    implements(IRequestFilter, IRequestHandler, ITemplateProvider)
        
    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename 
        return [('citecode', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler 

    def post_process_request(self, req, template, data, content_type):
        #Chrome(self.env).add_jquery_ui(req)
        add_script(req, 'citecode/citecode.js')
        add_script_data(req,
                {
                    '_traccitecode': {
                        'newticket': req.href + '/citecode/newticket',
                    }
                }
        )
        return template, data, content_type

    # IRequestHandler methods

    def match_request(self, req):
        self.log.debug('match_request: path_info=' + req.path_info)
        return req.path_info.startswith('/citecode/newticket/')

    def process_request(self, req):
        self.log.debug('process_request: path_info=' + req.path_info)
        self.log.debug('process_request: query_string=' + req.query_string)
        self.log.debug('process_request: browser()=' + self.env.href.browser())

        path = os.path.relpath(req.path_info, '/citecode/newticket')
        path = os.path.relpath(path, self.env.href.browser())

        at_rev = "" 
        query = "" 
        line = ""
        qs = urlparse.parse_qs(req.query_string)
        if 'rev' in qs:
            rev = qs['rev'][0].encode()
            at_rev = '@' + rev
            query = '?rev=' + rev
        if 'L' in qs:
            line = '#L' + qs['L'][0].encode()
        
        req.redirect(req.href.newticket(
                summary = 'Comment on %s' % os.path.basename(path),
                description = """source:/%s%s%s:
[[CiteCode(/%s%s%s)]]

""" % (path, at_rev, line, path, query, line),
                preview = True,
        ))
