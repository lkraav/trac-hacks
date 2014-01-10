# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009 Justin Francis <jfrancis@justinfrancis.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re

from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase

CAMEL = r"!?(?<!/|\?|#)\b[A-Z][a-z]+(?:[A-Z][a-z]*[a-z/])+" \
        r"(?:#[A-Za-z0-9]+)?(?=\Z|\s|[.,;:!?\)}\]])"
FANCY = r"(\[wiki:([^\] ]+) *.*?\])"
EXCLUDE = r"(?s)(`[^`]*`)|(\[.*?\])|({{{.*?}}})"

camel_re = re.compile(CAMEL)
fancy_re = re.compile(FANCY)
exclude_re = re.compile(EXCLUDE)

wiki_sql = "SELECT name, text FROM wiki ORDER BY version DESC"
ticket_sql = """SELECT id, description FROM ticket
    UNION 
    SELECT ticket, newvalue FROM ticket_change WHERE field='comment'        
"""


def exec_wiki_sql(db):
    cursor = db.cursor()
    cursor.execute(wiki_sql)
    rs = [(name, text) for name, text in cursor]
    cursor.close()
    return rs


def exec_ticket_sql(db):
    cursor = db.cursor()
    cursor.execute(ticket_sql)
    rs = [(id, text) for id, text in cursor]
    cursor.close()
    return rs


class WantedPagesMacro(WikiMacroBase):
    """Lists all wiki pages that are linked but not created in wiki pages and
    tickets. Use `[[WantedPages(show_referrers)]]` to show referring pages."""

    index = {}

    def get_macros(self):
        return ['WantedPages', 'wantedPages']

    def expand_macro(self, formatter, name, content, args=None):
        show_referrers = content and 'show_referrers' in content.strip()
        return format_to_html(self.env, formatter.context,
                              self.build_wiki_text(show_referrers))
    
    def build_wiki_text(self, show_referrers=False):
        texts = []  # list of referrer link, wiki-able text tuples
        wanted_pages = {}  # referrers indexed by page
        wiki_pages = []  # list of wikiPages seen
        db = self.env.get_db_cnx()

        # query is ordered by latest version first
        for name, text in exec_wiki_sql(db):
            if name not in wiki_pages:
                wiki_pages.append(name)
                self.index[name] = name
                texts.append(('[wiki:%s]' % name, text))

        for id, text in exec_ticket_sql(db):
            texts.append(('#%s' % id, text))
        
        for referrer, text in texts:
            for link in self.find_broken_links(text):
                if link not in wanted_pages:
                    wanted_pages[link] = []
                wanted_pages[link].append(referrer)

        wiki_list = ''
        for page in sorted(wanted_pages.keys()):
            ref = ''
            if show_referrers:
                ref = ' (Linked from %s)' % ', '.join(wanted_pages[page])
            wiki_list = '%s  * [wiki:%s]%s\n' % (wiki_list, page, ref)

        return wiki_list

    def find_broken_links(self, text):
        wanted_pages = []

        # regex does not work well for nested blocks
        text = self.remove_blocks(text)
        matches = exclude_re.findall(text)
        for pre, bracket, block in matches:
            text = text.replace(pre, '')
            text = text.replace(block, '')
            if not bracket.startswith('[wiki:'):
                text = text.replace(bracket, '')

        matches = fancy_re.findall(text)
        for fullLink, page in matches:
            if page.find('#') != -1:
                page = page[:page.find('#')]

            if page not in self.index and page[0] != '!':
                wanted_pages.append(page)

            # remove so no CamelCase detected below
            text = text.replace(fullLink, '')

        matches = camel_re.findall(text)
        for page in matches:
            if page.find('#') != -1:
                page = page[:page.find('#')]

            if page not in self.index and page[0] != '!':
                wanted_pages.append(page)
                
        return wanted_pages

    def remove_blocks(self, text):
        while text.find('{{{') >= 0:
            clear, rem = text.split('{{{', 1)            
            rem = self._extract_block(rem)
            text = clear + rem

        return text

    def _extract_block(self, s):
        if s.find('{{{') >= 0 and s.find('{{{') < s.find('}}}'):
            first, second = s.split('{{{', 1)
            s = self._extract_block(second)

        if s.find('}}}') >= 0:
            inside, outside = s.split('}}}', 1)
            cleaned = outside
        else:
            cleaned = s  # no closing braces

        return cleaned
