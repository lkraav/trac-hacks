#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from trac.core import Component, implements
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import prevnext_nav, add_link
from trac.wiki.api import WikiSystem, IWikiMacroProvider, parse_args


class NeighborPage(Component):
    """ Add 'Previous Page / Next Page' link to wiki navigation bar"""
    implements(IRequestFilter)

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
                if index > 0:
                    add_link(req, 'prev', req.href.wiki(pages[index - 1]))
                if index < len(pages) - 1:
                    add_link(req, 'next', req.href.wiki(pages[index + 1]))
                prevnext_nav(req, _('Previous Page'), _('Next Page'))
        return template, data, content_type


class Macro(Component):
    """ Generate Previous / Next Page link in place."""
    implements(IWikiMacroProvider)

    def get_macros(self):
            yield "SiblingPage"
            yield "PreviousPage"
            yield "NextPage"

    def get_macro_description(self, name):
        return "Generate Previous / Next Page link in place\n" \
               " ||= Wiki Markup =||= Display  =||\n" \
               " || {{{[[SiblingPage]]}}} || [[SiblingPage]]\n" \
               " || {{{[[SiblingPage(Prev, Next)]]}}} || [[SiblingPage(Prev, Next)]]\n" \
               " || {{{[[PreviousPage(Prev, Next)]]}}} || [[PreviousPage(Prev, Next)]]\n" \
               " || {{{[[SiblingPage($PageName)]]}}} || [[SiblingPage($PageName)]]\n" \
               " || {{{[[SiblingPage(Minutes($PageName))]]}}} || [[SiblingPage(Minutes($PageName))]]\n" \
               " arg **missing**: replacement for {{{$PageName}}} if next/previous page is not found"

    def expand_macro(self, formatter, name, content, args=None):
        content, args = parse_args(content)
        content = [len(content) == 0 and _('Previous Page') or content[0],
                   len(content) == 0 and _('Next Page') or len(content) == 1 and content[0] or content[1]]
        page = formatter.context.resource.id
        prefix = '/' in page and page[:page.rindex('/') + 1] or ''
        tier = prefix.count('/')
        wiki = WikiSystem(self.env)
        pages = sorted(page for page in wiki.get_pages(prefix) \
            if (page.count('/') == tier) \
            and 'WIKI_VIEW' in formatter.req.perm('wiki', page))
        if page in pages:
            result = tag.span()
            index = pages.index(page)
            missing = args and args.get('missing') or _('Missing Page')
            if name in ["SiblingPage", "PreviousPage"]:
                if index > 0:
                    result.append(tag.a(content[0].replace('$PageName', pages[index - 1]),
                                        href=formatter.req.href.wiki(pages[index - 1])))
                else:
                    result.append(tag.span(content[0].replace('$PageName', missing), class_='missing'))
            if name in ["SiblingPage"]:
                result.append(tag.span(' | ', style='color: #d7d7d7'))
            if name in ["SiblingPage", "NextPage"]:
                if index < len(pages) - 1:
                    result.append(tag.a(content[1].replace('$PageName', pages[index + 1]),
                                        href=formatter.req.href.wiki(pages[index + 1])))
                else:
                    result.append(tag.span(content[1].replace('$PageName', missing), class_='missing'))
            return result
