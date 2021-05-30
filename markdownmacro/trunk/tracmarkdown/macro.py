# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Douglas Clifton <dwclifton@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

""" @package MarkdownMacro
    @file macro.py
    @brief The markdownMacro class

    Implements Markdown syntax WikiProcessor as a Trac macro.

    From Markdown.py by Alex Mizrahi aka killer_storm
    See: http://trac-hacks.org/attachment/ticket/353/Markdown.py
    Get Python Markdown from:
        http://www.freewisdom.org/projects/python-markdown/

    @author Douglas Clifton <dwclifton@gmail.com>
    @date December, 2008
    @version 0.11.4
"""

from functools import partial
try:
    from markdown import markdown, Markdown
    from markdown.extensions import Extension
    from markdown.inlinepatterns import InlineProcessor
    from markdown import util
    from .wikiprocessor import WikiProcessorExtension, WikiProcessorFenceExtension
except ImportError:
    markdown = None

from trac.config import IntOption
from trac.core import Component, implements
from trac.util.html import Markup, html as tag, TracHTMLSanitizer
from trac.web.api import IRequestFilter
from trac.web.chrome import add_warning
from trac.wiki.api import WikiSystem
from trac.wiki.formatter import format_to_html, format_to_oneliner, Formatter, system_message
from trac.wiki.macros import WikiMacroBase

from .mdheader import HashHeaderProcessor


WARNING = tag('Error importing Python Markdown, install it from ',
              tag.a('here', href="https://pypi.python.org/pypi/Markdown"),
              '.')

tab_length = IntOption('markdown', 'tab_length', 4, """
    Specify the length of tabs in the markdown source. This affects
    the display of multiple paragraphs in list items, including sub-lists,
    blockquotes, code blocks, etc.
    """)

class MarkdownMacro(WikiMacroBase):
    """Implements Markdown syntax [WikiProcessors WikiProcessor] as a Trac
       macro."""

    tab_length = tab_length

    def expand_macro(self, formatter, name, content, args=None):
        if markdown:
            return format_to_markdown(self, formatter, content)
        else:
            return system_message(WARNING)


class MarkdownFormatter(Component):

    tab_length = tab_length

    implements(IRequestFilter)

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):

        def wiki_to_html(self, context, wikidom, escape_newlines=None):
            formatter = Formatter(self.env, context)
            return Markup(format_to_markdown(self, formatter, wikidom))

        if data:
            if markdown:
                data['wiki_to_html'] = partial(wiki_to_html, self)
            else:
                add_warning(req, WARNING)

        return template, data, content_type


def format_to_markdown(self, formatter, content):
    _sanitizer = TracHTMLSanitizer(
        safe_schemes=formatter.wiki.safe_schemes,
        safe_origins=formatter.wiki.safe_origins)

    def sanitize(text):
        if WikiSystem(self.env).render_unsafe_content:
            return Markup(text)
        else:
            return _sanitizer.sanitize(text)

    trac_link = TracLinkExtension()
    trac_macro = TracMacroExtension()
    trac_tkt = TracTicketExtension()
    wiki_proc = WikiProcessorExtension()
    wp_fence = WikiProcessorFenceExtension()

    md = Markdown(extensions=['extra', wiki_proc, trac_link, trac_macro, trac_tkt, wp_fence],
                  tab_length=self.tab_length, output_format='html')

    # Register our own blockprocessor for hash headers ('#', '##', ...) which adds
    # Tracs CSS classes for proper styling.
    md.parser.blockprocessors.deregister('hashheader')
    hash_header = HashHeaderProcessor(md.parser)  # This one is changed
    md.parser.blockprocessors.register(hash_header, 'hashheader', 70)

    # Added for use with format_to_html() and format_to_oneliner()
    md.trac_context = formatter.context
    md.trac_env = self.env
    return sanitize(md.convert(content))


class TracLinkInlineProcessor(InlineProcessor):
    """Render all kinds of Trac links ([wiki:...], [ticket:...], etc.).

    The Trac link is extracted from the text and converted using Tracs
    formatter to html. The html data is inserted eventually."""
    def handleMatch(self, m, data):
        if not m.group(1) or m.group(1)[0] == '[':
            # This is a Trac macro '[[FooBar()]]
            return None, None, None

        html = format_to_oneliner(self.md.trac_env, self.md.trac_context, '[%s]' % m.group(1))
        return self.md.htmlStash.store(html), m.start(0), m.end(0)


class TracLinkExtension(Extension):
    """For registering the Trac link processor"""

    TRAC_LINK_PATTERN = r'\[(.+?)\]'

    def extendMarkdown(self, md):
        # Use priority 115 so the markdown link processor with priority 160
        # may resolve links like [example](http://...) properly without our
        # extension breaking the link.
        # Same goes for shortrefs like [Google] with priority 130
        # and autolinks using priority 120.
        md.inlinePatterns.register(TracLinkInlineProcessor(self.TRAC_LINK_PATTERN, md), 'traclink', 115)


class TracMacroInlineProcessor(InlineProcessor):
    """Render Trac macros ('[FooBar()]').

    The macro is extracted from the text and formatted
    using Tracs wiki formatter.
    """
    def handleMatch(self, m, data):
        # This is a Trac macro '[[FooBar()]]
        # return None, None, None

        html = format_to_html(self.md.trac_env, self.md.trac_context, '[[%s]]' % m.group(1))
        return self.md.htmlStash.store(html), m.start(0), m.end(0)


class TracMacroExtension(Extension):
    """Register the Trac macro processor."""

    TRAC_MACRO_PATTERN = r'\[\[(.*?)\]\]'

    def extendMarkdown(self, md):
        md.inlinePatterns.register(TracMacroInlineProcessor(self.TRAC_MACRO_PATTERN, md), 'tracmacro', 172)


class TracTicketInlineProcessor(InlineProcessor):
    """Support simple Trac ticket links like '#123'."""
    def handleMatch(self, m, data):
        html = format_to_oneliner(self.md.trac_env, self.md.trac_context, '#%s' % m.group(1))
        return self.md.htmlStash.store(html), m.start(0), m.end(0)


class TracTicketExtension(Extension):
    """Register the ticket link extension."""

    TRAC_TICKET_PATTERN = r'#(\d+)'

    def extendMarkdown(self, md):
        # Use priority 115 so the markdown link processor with priority 160
        # may resolve links with location part like [example](http://example.com/foo#123) properly
        # without our extension breaking the link.
        # Same goes for autolinks <http://...> with priority 120.
        md.inlinePatterns.register(TracTicketInlineProcessor(self.TRAC_TICKET_PATTERN, md), 'tracticket', 115)
