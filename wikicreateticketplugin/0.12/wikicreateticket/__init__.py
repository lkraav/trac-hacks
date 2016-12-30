# -*- coding: utf-8 -*-

import re
from trac.core import Component, implements
from trac.wiki import IWikiChangeListener, WikiPage
from trac.ticket import Ticket

class WikiCreateTicket(Component):
    """create ticket from wiki."""

    implements(IWikiChangeListener)

    _new_ticket_re = re.compile(r'(?P<id>#new)\s+(?P<summary>.+?)\s*$',
                                re.UNICODE)
    _space_re = re.compile(r'\s', re.UNICODE)

    def wiki_page_added(self, page):
        self._parse_wiki_and_create_ticket(page, 1)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self._parse_wiki_and_create_ticket(page, version)

    def wiki_page_deleted(self, page):
        pass

    def wiki_page_version_deleted(self, page):
        pass

    def wiki_page_renamed(self, page, old_name):
        pass

    def _parse_wiki_and_create_ticket(self, page, version):
        page = WikiPage(self.env, page.name, version)

        lines = page.text.splitlines(True)
        for idx, line in enumerate(lines):
            match = self._new_ticket_re.search(line)
            if match:
                tktid = self.__create_new_ticket(page, match.group('summary'))
                if tktid:
                    lines[idx] = '%s#%d%s' % (line[:match.start('id')],
                                              tktid, line[match.end('id'):])
                else:
                    self.log.error("failed to create ticket from wiki: %s",
                                   page.name)

        self._update_wiki(page, ''.join(lines))

    def _update_wiki(self, page, text):
        @self.env.with_transaction()
        def fn(db):
            cursor = db.cursor()
            cursor.execute(
                "UPDATE wiki SET text=%s WHERE name=%s AND version=%s",
                (text, page.name, page.version))

    def __create_new_ticket(self, page, title):
        match = re.match(r'\[(\S+)\]\s*(.*?)\s*\Z', title)
        if match:
            summary = match.group(2)
            owner = match.group(1)
        else:
            summary = title
            owner = None
        ticket = Ticket(self.env)
        ticket['status'] = 'new'
        ticket['reporter'] = page.author
        ticket['summary'] = summary
        ticket['owner'] = owner
        if self._space_re.search(page.name):
            description = 'wiki:"%s"' % page.name
        else:
            description = 'wiki:%s' % page.name
        ticket['description'] = description
        return ticket.insert()
