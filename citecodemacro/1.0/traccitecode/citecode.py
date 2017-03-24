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

from trac.core import Component, implements
from trac.mimeview import Mimeview, Context
from trac.mimeview.api import is_binary
from trac.util.html import escape
from trac.web.chrome import add_script, add_script_data, add_stylesheet, ITemplateProvider
from trac.web.main import IRequestFilter, IRequestHandler
from trac.wiki.macros import WikiMacroBase
from trac.versioncontrol import RepositoryManager


class CiteCodeMacro(WikiMacroBase):
    def __init__(self):
        self.repoman = RepositoryManager(self.env)
        self.mimeview = Mimeview(self.env)

    def expand_macro(self, formatter, name, content):
        self.log.debug("content=%s" % content)

        add_stylesheet(formatter.req, 'citecode/citecode.css')

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
                        context.set_hints(lineno = int(start))
                xhtml = self.mimeview.render(
                        context = context,
                        mimetype = content_type,
                        content = content,
                        filename = "",
                        annotations=['citecode_lineno'],
                        )
                return xhtml
        finally:
            repo.close()

class CiteCodeAndCreateTicket(Component):

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
        return req.path_info == '/citecode/newticket'

    def process_request(self, req):
        path = req.args.get('path')
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
                description = """source:%s%s%s:

[[CiteCode(%s%s%s)]]

""" % (path, at_rev, line, path, query, line),
                preview = True,
        ))

from trac.mimeview.api import IHTMLPreviewAnnotator
from trac.util.translation import _
from trac.util import Ranges
from genshi.builder import tag

# Just copied from trunk of Trac core and renamed annotation_type
# since 'lineno' hint is not available in Trac 1.0

# Copyright (C) 2004-2014 Edgewall Software
# Copyright (C) 2004 Daniel Lundin <daniel@edgewall.com>
# Copyright (C) 2005-2006 Christopher Lenz <cmlenz@gmx.de>
# Copyright (C) 2006-2007 Christian Boos <cboos@edgewall.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Daniel Lundin <daniel@edgewall.com>
#         Christopher Lenz <cmlenz@gmx.de>
#         Christian Boos <cboos@edgewall.org>

class LineNumberAnnotator(Component):
    """Text annotator that adds a column with line numbers."""
    implements(IHTMLPreviewAnnotator)

    # IHTMLPreviewAnnotator methods

    def get_annotation_type(self):
        return 'citecode_lineno', _('Line'), _('Line numbers')

    def get_annotation_data(self, context):
        try:
            marks = Ranges(context.get_hint('marks'))
        except ValueError:
            marks = None
        return {
            'id': context.get_hint('id', '') + 'L%s',
            'marks': marks,
            'offset': context.get_hint('lineno', 1) - 1
        }

    def annotate_row(self, context, row, lineno, line, data):
        lineno += data['offset']
        id = data['id'] % lineno
        if data['marks'] and lineno in data['marks']:
            row(class_='hilite')
        row.append(tag.th(id=id)(tag.a(lineno, href='#' + id)))
