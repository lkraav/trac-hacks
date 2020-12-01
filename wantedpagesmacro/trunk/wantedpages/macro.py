# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009 Justin Francis <jfrancis@justinfrancis.org>
# Copyright (C) 2014 Geert Linders <glinders@dynamiccontrols.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import collections
import io
import time
import re

from trac.util.html import HTMLParser, Markup, escape
from trac.util.text import unicode_unquote
from trac.web.chrome import web_context
from trac.wiki.api import parse_args
from trac.wiki.formatter import HtmlFormatter, Formatter, format_to_html
from trac.wiki.macros import WikiMacroBase


# copied from trac/wiki/fomatter.py to use our HTML formatter
def format_to(env, context, wikidom, shorten=None):
    if not wikidom:
        return Markup()
    if shorten is None:
        shorten = context.get_hint('shorten_lines', False)
    # use our own HTML formatter
    return WantedPagesHtmlFormatter(env, context, wikidom).generate(shorten)


# subclass formatter so we can ignore content without links
class WantedPagesFormatter(Formatter):
    # override a few formatters to make formatting faster
    def __init__(self, env, context):
        super(WantedPagesFormatter, self).__init__(env, context)

    def _inlinecode_formatter(self, match, fullmatch):
        return ''

    def _inlinecode2_formatter(self, match, fullmatch):
        return ''

    def _macro_formatter(self, match, fullmatch, macro):
        return ''

    def handle_match(self, fullmatch):
        for itype, match in fullmatch.groupdict().items():
            if match:
                # ignore non-wiki references
                if (itype in ['lns', 'sns']) and (match != 'wiki'):
                    return ''
                # ignore Inter-Trac references and
                # references to tickets, changesets, etc.
                if (itype.startswith( 'it_')) or \
                    (itype in ['i3', 'i4', 'i5', 'i6']):
                    return ''
            if match and not itype in self.wikiparser.helper_patterns:
                # Check for preceding escape character '!'
                if match[0] == '!':
                    return escape(match[1:])
                if itype in self.wikiparser.external_handlers:
                    external_handler = self.wikiparser.external_handlers[itype]
                    return external_handler(self, match, fullmatch)
                else:
                    internal_handler = getattr(self, '_%s_formatter' % itype)
                    return internal_handler(match, fullmatch)


class WantedPagesHtmlFormatter(HtmlFormatter):
    # override to use our own HTML formatter
    def generate(self, escape_newlines=False):
        """Generate HTML inline elements.

        If `shorten` is set, the generation will stop once enough characters
        have been emitted.
        """
        # FIXME: compatibility code only for now
        out = io.StringIO()
        # use our own formatter
        WantedPagesFormatter(self.env, self.context).format(self.wikidom, out,
                                                            escape_newlines)
        return Markup(out.getvalue())


class MissingLinksHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.data = list()

    def reset(self):
        HTMLParser.reset(self)
        self.data = list()

    def handle_starttag(self, tag, attrs):
        # ignore all but links
        if tag != 'a':
            return
        _save = False
        _href = None
        for attr in attrs:
            # find missing wiki links
            if attr == ('class','missing wiki'):
                _save = True
            if attr[0] == 'href':
                _href = attr[1]
        if _save and _href:
            self.data.append(_href)


class WantedPagesMacro(WikiMacroBase):
    """Lists all wiki pages that are linked but not created in wiki pages.
    Use `[[WantedPages(show_referrers)]]` to show referring pages."""

    def get_macros(self):
        return ['WantedPages', 'wantedPages']

    def expand_macro(self, formatter, name, content, args=None):
        _start_time = time.time() # save start time
        _largs, _kwargs = parse_args(content)
        _show_referrers = _largs and 'show_referrers' in _largs
        _ignored_referrers = _kwargs.get('ignored_referrers', None)
        # 'filter' is an alias for option 'ignored_referrers'
        if not _ignored_referrers:
            _ignored_referrers = _kwargs.get('filter', None)
        # default option is 'exclusive' for backward compatibility
        _filtertype = _kwargs.get('filtertype', 'exclusive')
        _ml_parser = MissingLinksHTMLParser()
        _missing_links = collections.OrderedDict()

        for _name, _text in self.get_wiki_pages(_ignored_referrers, _filtertype):
            ctxt = web_context(formatter.req, 'wiki', _name)
            # parse formatted wiki page for missing links
            _ml_parser.feed(format_to(self.env, ctxt, _text))
            if _ml_parser.data:
                for _page in _ml_parser.data:
                    if _page in _missing_links:
                        if _missing_links[_page].count(_name) == 0:
                            _missing_links[_page] = _missing_links[_page] + \
                                                        [_name,]
                    else:
                        _missing_links[_page] = [_name,]
            _ml_parser.reset()

        if _show_referrers:
            _data ='||=Missing link=||=Referrer(s)=||\n'
        else:
            _data ='||=Missing link=||\n'
        _missing_link_count = 0
        for _page in _missing_links:
            _data = _data + '||[["%s"]]' % \
                        unicode_unquote(_page.partition('/wiki/')[2])
            if _show_referrers:
                _first = True
                for _name in _missing_links[_page]:
                    if _first:
                        _data = _data + '||[["%s"]]' % _name
                        _first = False
                    else:
                        _data = _data + ', [["%s"]]' % _name
                    _missing_link_count = _missing_link_count + 1
            _data = _data + "||\n"
        # reset context for relative links
        self.log.debug("Found %d missing pages in %s seconds'" % \
                       (_missing_link_count, (time.time() - _start_time)))
        return format_to_html(self.env, formatter.context, _data)

    def get_wiki_pages(self, ignored_referrers=None, filter='exclusive'):
        for name, text in self.env.db_query("""
                SELECT w1.name, w1.text FROM wiki w1,
                 (SELECT name, max(version) as max_version
                  FROM wiki GROUP BY name) w2
                WHERE w1.version = w2.max_version AND w1.name = w2.name
                """):
            if filter == 'exclusive':
                if ignored_referrers and re.search(ignored_referrers, name):
                    continue  # skip matching names
                else:
                    pass  # include non-matching names
            if filter == 'inclusive':
                if ignored_referrers and re.search(ignored_referrers, name):
                    pass  # include matching names
                else:
                    continue  # skip non-matching names
            yield name, text
