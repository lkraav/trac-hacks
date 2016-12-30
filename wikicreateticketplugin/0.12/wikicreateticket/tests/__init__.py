# -*- coding: utf-8 -*-

import inspect
import unittest

from trac.test import EnvironmentStub
from trac.ticket.model import Ticket
from trac.wiki.model import WikiPage

from wikicreateticket import WikiCreateTicket


class WikiCreateTicketTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.mod = WikiCreateTicket(self.env)

    def tearDown(self):
        self.env.reset_db()

    def _save_page(self, page, author, comment):
        args = [author, comment]
        if 'remote_addr' in inspect.getargspec(WikiPage.save)[0]:
            args.append('::1')
        @self.env.with_transaction()
        def create(db):
            page.save(*args)

    def test_page_created(self):
        page = WikiPage(self.env, 'TestPage')
        page.text = """\
= Test

 * #new Blah Blah Blah
 * #new [john] Blah Blah
"""
        self._save_page(page, 'anonymous', 'initial')
        self.mod.wiki_page_added(page)
        ticket = Ticket(self.env, 1)
        self.assertEqual('Blah Blah Blah', ticket['summary'])
        self.assertEqual('', ticket['owner'])
        self.assertEqual('anonymous', ticket['reporter'])
        self.assertEqual('wiki:TestPage', ticket['description'])
        ticket = Ticket(self.env, 2)
        self.assertEqual('Blah Blah', ticket['summary'])
        self.assertEqual('john', ticket['owner'])
        self.assertEqual('anonymous', ticket['reporter'])
        self.assertEqual('wiki:TestPage', ticket['description'])
        page = WikiPage(self.env, 'TestPage')
        page_text = """\
= Test

 * #1 Blah Blah Blah
 * #2 [john] Blah Blah
"""
        self.assertEqual(page_text, page.text)
        self.assertEqual(1, page.version)

    def test_page_changed(self):
        page = WikiPage(self.env, 'TestPage with spaces')
        page.text = "= Test\n"
        self._save_page(page, 'anonymous', 'initial')
        page.text = """\
= Test

 * #new [john] foobar
 * #new foobar foobar
"""
        self._save_page(page, 'anonymous', '2nd version')
        self.mod.wiki_page_changed(page, page.version, page.time,
                                   '2nd version', page.author, '::1')
        ticket = Ticket(self.env, 1)
        self.assertEqual('foobar', ticket['summary'])
        self.assertEqual('john', ticket['owner'])
        self.assertEqual('anonymous', ticket['reporter'])
        self.assertEqual('wiki:"TestPage with spaces"', ticket['description'])
        ticket = Ticket(self.env, 2)
        self.assertEqual('foobar foobar', ticket['summary'])
        self.assertEqual('', ticket['owner'])
        self.assertEqual('anonymous', ticket['reporter'])
        self.assertEqual('wiki:"TestPage with spaces"', ticket['description'])
        page = WikiPage(self.env, 'TestPage with spaces')
        page_text = """\
= Test

 * #1 [john] foobar
 * #2 foobar foobar
"""
        self.assertEqual(page_text, page.text)
        self.assertEqual(2, page.version)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WikiCreateTicketTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
