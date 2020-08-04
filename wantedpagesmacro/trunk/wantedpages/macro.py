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
from trac.wiki.api import parse_args
from trac.wiki.formatter import InlineHtmlFormatter, OneLinerFormatter, \
        format_to_html
from trac.wiki.parser import WikiParser
from trac.wiki.macros import WikiMacroBase


# copied from trac/wiki/fomatter.py to use our HTML formatter
def format_to_oneliner(env, context, wikidom, shorten=None):
    if not wikidom:
        return Markup()
    if shorten is None:
        shorten = context.get_hint('shorten_lines', False)
    # use our own HTML formatter
    return WantedPagesHtmlFormatter(env, context, wikidom).generate(shorten)


# Parse time is proportional to the number of regular expressions
# in the wiki parser. We subclass the wiki parser so we can remove
# all unwanted wiki markup to speed things up
class WantedPagesWikiParser(WikiParser):
    STARTBLOCK_TOKEN = WikiParser.STARTBLOCK_TOKEN
    ENDBLOCK_TOKEN = WikiParser.ENDBLOCK_TOKEN
    INLINE_TOKEN = WikiParser.INLINE_TOKEN
    LINK_SCHEME = WikiParser.LINK_SCHEME
    QUOTED_STRING = WikiParser.QUOTED_STRING
    SHREF_TARGET_FIRST = WikiParser.SHREF_TARGET_FIRST
    SHREF_TARGET_MIDDLE = WikiParser.SHREF_TARGET_MIDDLE
    SHREF_TARGET_LAST = WikiParser.SHREF_TARGET_LAST
    LHREF_RELATIVE_TARGET = WikiParser.LHREF_RELATIVE_TARGET
    XML_NAME = WikiParser.XML_NAME
    ENDBLOCK = WikiParser.ENDBLOCK
    STARTBLOCK = WikiParser.STARTBLOCK

    _pre_rules = [
        r"(?P<inlinecode>!?%s(?P<inline>.*?)%s)" \
        % (STARTBLOCK_TOKEN, ENDBLOCK_TOKEN),
        r"(?P<inlinecode2>!?%s(?P<inline2>.*?)%s)" \
        % (INLINE_TOKEN, INLINE_TOKEN),
        ]

    # Rules provided by IWikiSyntaxProviders will be inserted here

    _post_rules = [
        # <wiki:Trac bracket links>
        r"(?P<shrefbr>!?<(?P<snsbr>%s):(?P<stgtbr>[^>]+)>)" % LINK_SCHEME,
        # wiki:TracLinks or intertrac:wiki:TracLinks
        r"(?P<shref>!?((?P<sns>%s):(?P<stgt>%s:(?:%s)|%s|%s(?:%s*%s)?)))" \
        % (LINK_SCHEME, LINK_SCHEME, QUOTED_STRING, QUOTED_STRING,
           SHREF_TARGET_FIRST, SHREF_TARGET_MIDDLE, SHREF_TARGET_LAST),
        # [wiki:TracLinks with optional label] or [/relative label]
        (r"(?P<lhref>!?\[(?:"
         r"(?P<rel>%s)|" % LHREF_RELATIVE_TARGET + # ./... or /...
         r"(?P<lns>%s):(?P<ltgt>%s:(?:%s)|%s|[^\]\s\%s]*))" % \
         (LINK_SCHEME, LINK_SCHEME, QUOTED_STRING, QUOTED_STRING, u'\u200b') +
         # wiki:TracLinks or wiki:"trac links" or intertrac:wiki:"trac links"
         r"(?:[\s%s]+(?P<label>%s|[^\]]*))?\])" % \
         (u'\u200b', QUOTED_STRING)), # trailing space, optional label
        # [[macro]] call or [[WikiCreole link]]
        (r"(?P<macrolink>!?\[\[(?:[^]]|][^]])+\]\])"),
        ]
    pass


# subclass formatter so we can ignore content without links
class WantedPagesFormatter(OneLinerFormatter):
    # override a few formatters to make formatting faster
    def __init__(self, env, context):
        OneLinerFormatter.__init__(self, env, context)
        # use our own wiki parser
        self.wikiparser = WantedPagesWikiParser(self.env)

    def _inlinecode_formatter(self, match, fullmatch):
        return ''

    def _inlinecode2_formatter(self, match, fullmatch):
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


class WantedPagesHtmlFormatter(InlineHtmlFormatter):
    # override to use our own HTML formatter
    def generate(self, shorten=False):
        """Generate HTML inline elements.

        If `shorten` is set, the generation will stop once enough characters
        have been emitted.
        """
        # FIXME: compatibility code only for now
        out = io.StringIO()
        # use our own formatter
        WantedPagesFormatter(self.env, self.context).format(self.wikidom, out,
                                                         shorten)
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
        if tag != 'a': return
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
        # get all wiki page names and their content
        self.page_names, self.page_texts = \
            self.get_wiki_pages(_ignored_referrers, _filtertype)
        _ml_parser = MissingLinksHTMLParser()
        # OrderedDict is needed to run test cases, but was only added in Python 2.7
        try:
            _missing_links = collections.OrderedDict()
        except:
            _missing_links = dict()

        for _name, _text in zip(self.page_names, self.page_texts):
            # set up context for relative links
            formatter.resource.id = _name
            # parse formatted wiki page for missing links
            _ml_parser.feed(format_to_oneliner(self.env, formatter.context,
                                               _text))
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
                        _page.partition('/wiki/')[2].replace('%20',' ')
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
        formatter.resource.id = ''
        self.log.debug("Found %d missing pages in %s seconds'" % \
                       (_missing_link_count, (time.time() - _start_time)))
        return format_to_html(self.env, formatter.context, _data)

    def get_wiki_pages(self, ignored_referrers=None, filter='exclusive'):
        page_texts = [] # list of referrer link, wiki-able text tuples
        page_names = [] # list of wikiPages seen

        # query is ordered by latest version first
        # so it's easy to extract the latest pages
        for name, text in self.env.db_query("""
                SELECT name, text FROM wiki ORDER BY version DESC
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
            if name not in page_names:
                page_names.append(name)
                page_texts.append(text)
        return page_names, page_texts
