#!/usr/bin/env python
# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import prevnext_nav, add_link
from trac.wiki.api import WikiSystem

class NeighborPage(Component):
    """ Add 'previous page / next page' link to wiki navigation bar"""
    implements (IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if data and 'context' in data and \
                data['context'].resource.realm == 'wiki' and \
                'action' not in req.args and \
                'version' not in req.args:
            page = data['page']
            prefix = '/' in page.name and page.name[:page.name.rindex('/') + 1] or ''
            wiki = WikiSystem(self.env)
            start = prefix.count('/')
            pages = sorted(page for page in wiki.get_pages(prefix) \
                   if (start >= page.count('/'))
                   and 'WIKI_VIEW' in req.perm('wiki', page))
            if page.name in pages:
                index = pages.index(page.name)
                if index > 0: add_link(req, 'prev', req.href.wiki(pages[index - 1]))
                if index < len(pages) - 1: add_link(req, 'next', req.href.wiki(pages[index + 1]))
                prevnext_nav(req, _('previous page'), _('next page'))
        return template, data, content_type
    
    
