# -*- coding: utf-8 -*-
# List all Trac Plugins in a parent directory.

import os
from urlparse import urljoin

from genshi.builder import tag
from trac.config import Option
from trac.wiki.macros import WikiMacroBase

class ListTracProjectsMacro(WikiMacroBase):

    base_dir = Option('projects', 'base_dir',
        doc="""Base directory for Trac projects.""")

    base_url = Option('projects', 'base_url',
        doc="""Base URL for Trac projects.""")

    def expand_macro(self, formatter, name, content, args=None):
        out = tag()

        if self.base_url:
            href = self.base_url
        elif formatter.req.base_path:
            href = formatter.req.abs_href().rsplit('/', 1)[0]
        else:
            href = formatter.req.abs_href()
        for i, f in enumerate(os.listdir(self.base_dir)):
            if i != 0:
                out.append(" :: ")
            out.append(tag.a(f, href=urljoin(href, f), target='_new'))
        return out
