# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 Martin Scharrer <martin@scharrer-online.de>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from trac.test import EnvironmentStub, Mock, MockPerm, locale_en
from trac.ticket.roadmap import MilestoneModule
from trac.util.datefmt import utc
from trac.web.api import _RequestArgs, RequestDone
from trac.wiki.model import WikiPage
from trac.wiki.tests import formatter
from trac.wiki.web_ui import WikiModule

from tracserversideredirect.plugin import ServerSideRedirectPlugin


MACRO_TEST_CASES = u"""\
============================== # Wiki TracLink
[[Redirect(OtherWikiPage)]]
------------------------------
<p>
</p><div class="system-message" id="notice">\
<strong>This page redirects to: </strong>\
<a href="/wiki/OtherWikiPage">OtherWikiPage</a>\
</div><p>
</p>
============================== # Wiki TracLink with wiki prefix
[[Redirect(wiki:OtherWikiPage)]]
------------------------------
<p>
</p><div class="system-message" id="notice">\
<strong>This page redirects to: </strong>\
<a href="/wiki/OtherWikiPage">wiki:OtherWikiPage</a>\
</div><p>
</p>
============================== # InterTrac to wiki
[[Redirect(trac:OtherWikiPage)]]
------------------------------
<p>
</p><div class="system-message" id="notice">\
<strong>This page redirects to: </strong>\
<a href="http://trac.edgewall.org/intertrac/OtherWikiPage">trac:OtherWikiPage</a>\
</div><p>
</p>
============================== # InterTrac with wiki prefix
[[Redirect(trac:wiki:OtherWikiPage)]]
------------------------------
<p>
</p><div class="system-message" id="notice">\
<strong>This page redirects to: </strong>\
<a href="http://trac.edgewall.org/intertrac/wiki%3AOtherWikiPage">trac:wiki:OtherWikiPage</a>\
</div><p>
</p>
============================== # Milestone TracLink
[[Redirect(milestone:milestone1)]]
------------------------------
<p>
</p><div class="system-message" id="notice">\
<strong>This page redirects to: </strong>\
<a href="/milestone/milestone1">milestone:milestone1</a>\
</div><p>
</p>
============================== # External URL
[[Redirect(http://www.example.com/)]]
------------------------------
<p>
</p><div class="system-message" id="notice">\
<strong>This page redirects to: </strong>\
<a href="http://www.example.com/">http://www.example.com/</a>\
</div><p>
</p>
"""


def macro_setup(tc):
    tc.env.enable_component(ServerSideRedirectPlugin)


class RequestHandlerTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.redirect_target = None

    def _create_page(self, text):
        page = WikiPage(self.env, 'ThePage')
        page.text = text
        page.save('anonymous', 'the comment')
        return page

    def _create_request(self, **kwargs):
        kw = {'path_info': '/wiki/ThePage', 'perm': MockPerm(),
              'args': _RequestArgs(), 'href': self.env.href,
              'abs_href': self.env.abs_href, 'tz': utc, 'locale': None,
              'lc_time': locale_en, 'session': {}, 'authname': 'anonymous',
              'chrome': {'notices': [], 'warnings': []}, 'method': 'GET',
              'environ': {'HTTP_REFERER': ''}, 'get_header': lambda v: None,
              'is_xhr': False, 'form_token': None}
        if 'args' in kwargs:
            kw['args'].update(kwargs.pop('args'))
        kw.update(kwargs)

        def redirect(url, permanent=False):
            self.redirect_target = url
            raise RequestDone

        return Mock(add_redirect_listener=lambda x: [].append(x),
                    redirect=redirect, **kw)

    def _test_redirect(self):
        req = self._create_request()

        ssrp = ServerSideRedirectPlugin(self.env)
        handler = ssrp.pre_process_request(req, WikiModule(self.env))

        self.assertTrue(isinstance(handler, ServerSideRedirectPlugin))
        self.assertRaises(RequestDone, ssrp.process_request, req)

    def test_redirect_to_page(self):
        self._create_page("[[Redirect(OtherWikiPage)]]")
        self._test_redirect()
        self.assertEqual('/trac.cgi/wiki/OtherWikiPage'
                         '?redirectedfrom=ThePage', self.redirect_target)

    def test_redirect_to_page_with_wiki_prefix(self):
        self._create_page("[[Redirect(wiki:OtherWikiPage)]]")
        self._test_redirect()
        self.assertEqual('/trac.cgi/wiki/OtherWikiPage'
                         '?redirectedfrom=ThePage', self.redirect_target)

    def test_redirect_to_intertrac_page(self):
        self._create_page("[[Redirect(trac:OtherWikiPage)]]")
        self._test_redirect()
        self.assertEqual('http://trac.edgewall.org/intertrac/OtherWikiPage',
                         self.redirect_target)

    def test_redirect_to_intertrac_page_with_wiki_prefix(self):
        self._create_page("[[Redirect(trac:wiki:OtherWikiPage)]]")
        self._test_redirect()
        self.assertEqual('http://trac.edgewall.org/intertrac/'
                         'wiki%3AOtherWikiPage', self.redirect_target)

    def test_redirect_to_source_browser(self):
        self._create_page("[[Redirect(milestone:milestone1)]]")
        self._test_redirect()
        self.assertEqual('/trac.cgi/milestone/milestone1'
                         '?redirectedfrom=ThePage', self.redirect_target)

    def test_redirect_to_external(self):
        self._create_page("[[Redirect(http://www.example.com/)]]")
        self._test_redirect()
        self.assertEqual('http://www.example.com/', self.redirect_target)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.suite(MACRO_TEST_CASES, file=__file__,
                                  setup=macro_setup))
    suite.addTest(unittest.makeSuite(RequestHandlerTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
