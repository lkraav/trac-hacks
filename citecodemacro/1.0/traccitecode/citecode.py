# -*- coding: utf-8 -*-

import re
import urlparse
import mimetypes

from genshi.core import escape
from trac.mimeview import Mimeview, Context
from trac.mimeview.api import is_binary
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
            if qs.has_key('rev') == None:
                rev = None
            else:
                rev = qs['rev'][0].encode()
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
