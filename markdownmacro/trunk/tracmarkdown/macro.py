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

import re
from io import StringIO
try:
    from markdown import markdown, Markdown
    from markdown.inlinepatterns import InlineProcessor
    from markdown.extensions import Extension
    from markdown import util
except ImportError:
    markdown = None

from trac.config import IntOption
from trac.core import Component, implements
from trac.util.html import Markup, html as tag
from trac.web.api import IRequestFilter
from trac.web.chrome import add_warning
from trac.wiki.formatter import format_to_html, format_to_oneliner, Formatter, system_message
from trac.wiki.macros import WikiMacroBase

from .mdheader import HashHeaderProcessor

# links, autolinks, and reference-style links

LINK = re.compile(
    r'(\[.*\]\()([^) ]+)([^)]*\))|(<)([^>]+)(>)|(\n\[[^]]+\]: *)([^ \n]+)(.*\n)'
)
HREF = re.compile(r'href=[\'"]?([^\'" ]*)', re.I)
WARNING = tag('Error importing Python Markdown, install it from ',
              tag.a('here', href="https://pypi.python.org/pypi/Markdown"),
              '.')


class MarkdownMacro(WikiMacroBase):
    """Implements Markdown syntax [WikiProcessors WikiProcessor] as a Trac
       macro."""

    tab_length = IntOption('markdown', 'tab_length', 4, """
        Specify the length of tabs in the markdown source. This affects
        the display of multiple paragraphs in list items, including sub-lists,
        blockquotes, code blocks, etc.
        """)

    def expand_macro(self, formatter, name, content, args=None):
        if markdown:
            return format_to_markdown(self.env, formatter.context, content)
        else:
            return system_message(WARNING)


class MarkdownFormatter(Component):

    implements(IRequestFilter)

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):

        def wiki_to_html(context, wikidom, escape_newlines=None):
            return Markup(format_to_markdown(self.env, context, wikidom))

        if data:
            if markdown:
                data['wiki_to_html'] = wiki_to_html
            else:
                add_warning(req, WARNING)

        return template, data, content_type


def format_to_markdown(env, context, content):
    abs_href = env.abs_href.base
    abs_href = abs_href[:len(abs_href) - len(env.href.base)]
    f = Formatter(env, context)
    tab_length = env.config.getint('markdown', 'tab_length')

    def convert(m):
        pre, target, suf = filter(None, m.groups())
        out = StringIO()
        f.format(target, out)
        out_value = out.getvalue()
        # Render obfuscated emails without a link
        if u'…' in out_value:
            idx = out_value.find('mailto:')
            if idx != -1:
                out_value = out_value[:idx-1] + out_value[idx+7:]
            return out_value
        else:
            match = re.search(HREF, out_value)
            if match:
                url = match.group(1)
                # Trac creates relative links, which Markdown won't touch
                # inside <autolinks> because they look like HTML
                if pre == '<' and url != target:
                    pre += abs_href
                return pre + str(url) + suf

    trac_link = TracLinkExtension()
    trac_makro = TracMakroExtension()
    md = Markdown(extensions=['tables', trac_link, trac_makro], tab_length=tab_length, output_format='html')

    # Register our own blockprocessor for hash headers ('#', '##', ...) which adds
    # Tracs CSS classes for proper styling.
    md.parser.blockprocessors.deregister('hashheader')
    hash_header = HashHeaderProcessor(md.parser)  # This one is changed
    md.parser.blockprocessors.register(hash_header, 'hashheader', 70)

    # Added for use with format_to_html() and format_to_oneliner()
    md.trac_context = context
    md.trac_env = env
    return md.convert(re.sub(LINK, convert, content))


class TracLinkInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        if m.group(1)[0] == '[':
            # This is a Trac makro '[[FooBar()]]
            return None, None, None

        # print('Trac groups: ', m.groups())
        html = format_to_oneliner(self.md.trac_env, self.md.trac_context, '[%s]' % m.group(1))
        return self.md.htmlStash.store(html), m.start(0), m.end(0)

        # el = util.etree.Element('span')
        # el.text = self.md.htmlStash.store(html)
        # return el, m.start(0), m.end(0)


TRAC_LINK_PATTERN = r'\[(.*?)\]'
class TracLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(TracLinkInlineProcessor(TRAC_LINK_PATTERN, md), 'traclink', 170)


class TracMakroInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        # This is a Trac makro '[[FooBar()]]
        # return None, None, None

        html = format_to_html(self.md.trac_env, self.md.trac_context, '[[%s]]' % m.group(1))
        return self.md.htmlStash.store(html), m.start(0), m.end(0)


TRAC_MAKRO_PATTERN = r'\[\[(.*?)\]\]'
class TracMakroExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(TracMakroInlineProcessor(TRAC_MAKRO_PATTERN, md), 'tracmakro', 172)
