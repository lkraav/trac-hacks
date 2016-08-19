# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import urllib2
import uuid
from genshi.core import escape
from trac.core import implements
from trac.web.chrome import add_script, add_script_data, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.wiki.api import IWikiPageManipulator
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

class MermaidMacro(WikiMacroBase):
    implements(ITemplateProvider, IRequestHandler, IWikiPageManipulator)

    def expand_macro(self, formatter, name, content, args=None):
        self.log.debug("content=%s" % content)
        add_script(formatter.req, 'mermaid/mermaid.min.js')
        add_script(formatter.req, 'mermaid/tracmermaid.js')
        add_script_data(formatter.req,
                {
                    '_tracmermaid': {
                        'submit': formatter.req.href + '/mermaid/submit',
                    }
                }
        )
        if args == None or 'id' not in args:
            id_attr = ''
        else:
            id_attr = 'id=%s' % args['id']
        url_escaped_content = urllib2.quote(content)
        div = """<div class="mermaid"
                      %s
                      data-mermaidresourcerealm="%s"
                      data-mermaidresourceid="%s"
                      data-mermaidresourceversion="%s"
                      data-mermaidsource="%s">%s</div>"""
        return div % (
                id_attr,
                formatter.context.resource.realm,
                formatter.context.resource.id,
                formatter.context.resource.version or '',
                escape(url_escaped_content),
                escape(content))

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename 
        return [('mermaid', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestHandler methods

    def match_request(self, req):
        self.log.debug('match_request: path_info=' + req.path_info)
        return req.path_info.startswith('/mermaid/submit')

    def process_request(self, req):
        self.log.debug('process_request: req=' + str(req))
        self.log.debug('process_request: args=' + str(req.args))

        id = req.args['id']
        page_name = req.args['wikipage']
        source = req.args['source']
        page = WikiPage(env = self.env, name = page_name)
        lines = page.text.splitlines()
        lines.reverse()
        buf = []
        while len(lines) > 0:
            line = lines.pop()
            if line == ('{{{#!Mermaid id="%s"' % id):
                buf.append(line)
                buf.append(source)
                while len(lines) > 0:
                    line = lines.pop()
                    if line.rstrip() == "}}}":
                        buf.append(line)
                        break
            else:
                buf.append(line)
        page.text = "\n".join(buf)

        req.perm(page).require('WIKI_MODIFY')
        comment = "Update from Mermaid live editor"
        page.save(req.authname, comment, req.remote_addr)

        req.send("OK", 'text/plain')

    # IWikiPageManipulator methods

    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        buf = []
        for line in page.text.splitlines():
            if line == "{{{#!Mermaid":
                buf.append('{{{#!Mermaid id="%s"' % str(uuid.uuid1()))
            else:
                buf.append(line)
        page.text = "\n".join(buf)
        return []
