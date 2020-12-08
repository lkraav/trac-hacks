# -*- coding: utf-8 -*-
#
# BackLinks plugin for Trac
#
# Author: Trapanator trap@trapanator.com
# Website: http://www.trapanator.com/blog/archives/category/trac
# License: GPL 3.0
#

import re
from StringIO import StringIO

from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage


class BackLinksListMacro(WikiMacroBase):
    """
    Inserts a list of all wiki pages with links to the page where this
    macro is used with a cleaner look.

    Accepts a page name as a parameter: if provided, pages that link to the
    provided page name are listed instead.
    """

    def expand_macro(self, formatter, name, args):

        caller_page = WikiPage(self.env, formatter.context.resource).name
        backlinks_page = args or caller_page

        backlinked_pages = \
            _get_backlinked_pages(self.env, caller_page, backlinks_page)

        buf = StringIO()
        if backlinked_pages:
            last_page = backlinked_pages.pop()
            for page in backlinked_pages:
                buf.write('<a href="%s">' % formatter.req.href.wiki(page))
                buf.write(page)
                buf.write('</a>, ')
            buf.write('<a href="%s">' % formatter.req.href.wiki(last_page))
            buf.write(last_page)
            buf.write('</a>')

        return buf.getvalue()


class BackLinksMacro(WikiMacroBase):
    """
    Inserts a list of all wiki pages with links to the page where this
    macro is used.

    Accepts a page name as a parameter: if provided, pages that link to the
    provided page name are listed instead.
    """

    def expand_macro(self, formatter, name, args):

        caller_page = WikiPage(self.env, formatter.context.resource).name
        backlinks_page = args or caller_page

        backlinked_pages = \
            _get_backlinked_pages(self.env, caller_page, backlinks_page)

        buf = StringIO()
        if backlinked_pages:
            buf.write('<hr style="width: 10%; padding: 0; margin: 2em 0 1em 0;"/>')
            buf.write('Pages linking to %s:\n' % backlinks_page)
            buf.write('<ul>')
            for page in backlinked_pages:
                buf.write('<li><a href="%s">' % formatter.req.href.wiki(page))
                buf.write(page)
                buf.write('</a></li>\n')
            buf.write('</ul>')

        return buf.getvalue()


class BackLinksMenuMacro(WikiMacroBase):
    """
    Inserts a menu with a list of all wiki pages with links to the page where
    this macro is used.

    Accepts a page name as a parameter: if provided, pages that link to the
    provided page name are listed instead.
    """

    def expand_macro(self, formatter, name, args):

        caller_page = WikiPage(self.env, formatter.context.resource).name
        backlinks_page = args or caller_page

        backlinked_pages = \
            _get_backlinked_pages(self.env, caller_page, backlinks_page)

        buf = StringIO()
        if backlinked_pages:
            buf.write('<div class="wiki-toc backlinks-menu">')
            buf.write('Pages linking to %s:<br />\n' % backlinks_page)
            for page in backlinked_pages:
                buf.write('<a href="%s">' % formatter.req.href.wiki(page))
                buf.write(page)
                buf.write('</a><br />\n')
            buf.write('</div>')

        return buf.getvalue()


def _get_backlinked_pages(env, caller_page, backlinks_page):

    backlinked_pages = []
    re_pattern = re_search_pattern(backlinks_page)
    like_pattern = sql_search_pattern(backlinks_page)
    with env.db_query as db:
        for page, text in db("""
                SELECT w1.name, w1.text FROM wiki AS w1,
                 (SELECT name, MAX(version) AS version
                  FROM wiki GROUP BY name) AS w2
                WHERE w1.version = w2.version AND w1.name = w2.name AND
                (w1.text %s)""" % db.like(),
                ('%' + db.like_escape(like_pattern) + '%',)):
            if page != backlinks_page and page != caller_page \
                    and re_pattern.search(text):
                backlinked_pages.append(page)

    return backlinked_pages


def sql_search_pattern(backlinks_page):
    if is_camel_case(backlinks_page):
        return backlinks_page
    else:
        return r'wiki:%s' % backlinks_page


def re_search_pattern(backlinks_page):
    if is_camel_case(backlinks_page):
        pattern = r'\b%s\b' % re.escape(backlinks_page)
    else:
        pattern = r'(\b|\[)wiki:%s(\b|\])' % re.escape(backlinks_page)
    return re.compile(pattern, re.UNICODE)


def is_camel_case(backlinks_page):
    words = camel_case_split(backlinks_page)
    if len(words) < 2:
        return False
    for word in words:
        if len(word) < 2:
            return False
    return True


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]
