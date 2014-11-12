# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub
from trac.ticket.model import Component, Ticket
from trac.wiki.model import WikiPage
from trac.wiki.tests import formatter

import trachacks.macros


MAINTAINER_MACRO_WIKI_TEST_CASE = u"""
==============================
[[Maintainer]]
------------------------------
<p>
<a class="missing wiki" href="/wiki/mrenzmann" rel="nofollow">mrenzmann?</a>
</p>
------------------------------
==============================
[[Maintainer(TracHacksPlugin)]]
------------------------------
<p>
<a class="missing wiki" href="/wiki/mrenzmann" rel="nofollow">mrenzmann?</a>
</p>
------------------------------
==============================
[[Maintainer(FullBlogPlugin)]]
------------------------------
<p>
<a class="wiki" href="/wiki/osimons">osimons</a>
</p>
------------------------------
==============================
[[Maintainer(AccountManagerPlugin)]]
------------------------------
<p>
<em>Component "AccountManagerPlugin" does not exist</em>
</p>
------------------------------
==============================
[[Maintainer(MilestoneMacro)]]
------------------------------
<p>
<em>none ([tag:needsadoption])</em>
</p>
------------------------------
==============================
[[Maintainer(TracHacksPlugin, owner)]]
------------------------------
<p>
<div class="system-message"><strong>Error: Macro Maintainer(TracHacksPlugin, owner) failed</strong><pre>Invalid number of arguments</pre></div>
</p>
------------------------------
"""


MAINTAINER_MACRO_TICKET_TEST_CASE = u"""
==============================
[[Maintainer]]
------------------------------
<p>
<div class="system-message"><strong>Error: Macro Maintainer(None) failed</strong><pre>Hack name must be specified as argument when the context realm is not \'wiki\'</pre></div>
</p>
------------------------------
==============================
[[Maintainer(TracHacksPlugin)]]
------------------------------
<p>
<a class="missing wiki" href="/wiki/mrenzmann" rel="nofollow">mrenzmann?</a>
</p>
------------------------------
==============================
[[Maintainer(FullBlogPlugin)]]
------------------------------
<p>
<a class="wiki" href="/wiki/osimons">osimons</a>
</p>
------------------------------
==============================
[[Maintainer(AccountManagerPlugin)]]
------------------------------
<p>
<em>Component "AccountManagerPlugin" does not exist</em>
</p>
------------------------------
"""


def setup(tc):
    tc.env = EnvironmentStub(enable=['trac.*', 'trachacks.*'])
    component1 = Component(tc.env)
    component1.name = 'TracHacksPlugin'
    component1.owner = 'mrenzmann'
    component1.insert()
    component2 = Component(tc.env)
    component2.name = 'FullBlogPlugin'
    component2.owner = 'osimons'
    component2.insert()
    component3 = Component(tc.env)
    component3.name = 'MilestoneMacro'
    component3.insert()
    ticket = Ticket(tc.env)
    ticket['summary'] = 'Ticket summary'
    ticket['reporter'] = 'hasienda'
    ticket.insert()
    page = WikiPage(tc.env, 'osimons')
    page.text = 'osimons'
    page.save('osimons', '', '127.0.0.1')


def teardown(tc):
    tc.env.reset_db()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.suite(MAINTAINER_MACRO_WIKI_TEST_CASE, setup,
                                  __file__, teardown,
                                  ('wiki', 'TracHacksPlugin')))
    suite.addTest(formatter.suite(MAINTAINER_MACRO_TICKET_TEST_CASE,
                                  setup, __file__, teardown,
                                  ('ticket', 1)))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
