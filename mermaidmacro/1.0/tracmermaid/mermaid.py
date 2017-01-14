# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
import urllib2
import uuid

from trac.core import implements
from trac.util.text import unicode_quote
from trac.util.html import Fragment, Element, Markup, escape
from trac.web.chrome import (add_script, add_script_data, add_stylesheet,
                             Chrome, ITemplateProvider)
from trac.web.main import IRequestHandler
from trac.wiki.api import IWikiPageManipulator
from trac.wiki.formatter import extract_link
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage


class MermaidMacro(WikiMacroBase):
    implements(ITemplateProvider, IRequestHandler, IWikiPageManipulator)

    def expand_macro(self, formatter, name, content, args=None):
        self.log.debug("content %s", content)
        context = formatter.context
        req = formatter.req
        if args is None or 'id' not in args:
            id_attr = ''
        else:
            id_attr = 'id="%s"' % escape(args['id'])
        if not req:
            # Off-line rendering (there's a command line API for mermaid)
            return '<img alt="not-yet-implemented"/>'
        Chrome(self.env).add_jquery_ui(req)
        add_stylesheet(req, 'mermaid/mermaid.css')
        add_script(req, 'mermaid/mermaid.min.js')
        add_script(req, 'mermaid/tracmermaid.js')
        add_script_data(req,
                {
                    '_tracmermaid': {
                        'submit': req.href + '/mermaid/submit',
                    },
                    'form_token': req.form_token,
                }
        )
        content = self.expand_links(context, content)
        return """\
            <div class="mermaid"
                       %s
                       data-mermaidresourcerealm="%s"
                       data-mermaidresourceid="%s"
                       data-mermaidresourceversion="%s"
                       data-mermaidsource="%s">%s
            </div>
            <script type="text/javascript">
                if (typeof mermaid !== 'undefined') {
                    mermaid.init(); // ok to call repeatedly (data-processed)
                    $(".mermaid g[title]").css('cursor', 'pointer');
                }
            </script>""" % (
                id_attr,
                escape(context.resource.realm),
                escape(context.resource.id),
                escape(context.resource.version or ''),
                escape(unicode_quote(content)),
                escape(content))

    click_re = re.compile(r'^\s*click\s+\w+\s+(trac)\s+(.*)$')

    def expand_links(self, context, content):
        lines = []
        for line in content.splitlines():
            # "Native" mermaid link (left alone):
            #   click A callback "This is a tooltip for a link"
            #   click B "http://www.github.com" "This is a tooltip for a link"
            #
            # TracLinks link (transformed to native):
            #   click A trac TracLinks
            #   click A trac r123
            #   click A trac [123]
            #   click A trac [[TracLinks|Anything that can be parsed as a link]]
            m = self.click_re.match(line)
            if m:
                link = m.group(2)
                link = extract_link(self.env, context, link)
                if isinstance(link, Element):
                    href = link.attrib.get('href')
                    title = link.attrib.get('title', '')
                    for c in link.children:
                        if not isinstance(c, Fragment):
                            name = c
                            break
                    else:
                        name = description
                    line = line[0:m.start(1)] + '"%s" "%s"' % (
                        href.replace('"', ''), name.replace('"', ''))
            lines.append(line)
        return '\n'.join(lines)

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
