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
from trac.web.session import DetachedSession
from trac.wiki.model import WikiPage
from trac.wiki.tests import formatter

import trachacks.macros
from tractags.db import TagSetup
from tractags.model import tag_resource


MAINTAINER_MACRO_WIKI_TEST_CASE = u"""
==============================
[[Maintainer]]
------------------------------
<p>
<a class="missing wiki" href="/wiki/mrenzmann" rel="nofollow">mrenzmann?</a>
</p>
==============================
[[Maintainer(TracHacksPlugin)]]
------------------------------
<p>
<a class="missing wiki" href="/wiki/mrenzmann" rel="nofollow">mrenzmann?</a>
</p>
==============================
[[Maintainer(FullBlogPlugin)]]
------------------------------
<p>
<a class="wiki" href="/wiki/osimons">osimons</a>
</p>
==============================
[[Maintainer(TracMigratePlugin)]]
------------------------------
<p>
<a class="wiki" href="/wiki/jun66j5">Jun Omae</a>
</p>
==============================
[[Maintainer(AccountManagerPlugin)]]
------------------------------
<p>
<em>Component "AccountManagerPlugin" does not exist</em>
</p>
==============================
[[Maintainer(MilestoneMacro)]]
------------------------------
<p>
<em>none ([tag:needsadoption])</em>
</p>
==============================
[[Maintainer(TracHacksPlugin, owner)]]
------------------------------
<p>
</p><div class="system-message"><strong>Maintainer macro error</strong>\
<pre>Invalid number of arguments</pre></div><p>
</p>
==============================
[[Maintainer(DeprecatedMacro)]]
------------------------------
<p>
<em>none ([tag:deprecated])</em>
</p>
==============================
[[Maintainer(DeprecatedPlugin)]]
------------------------------
<p>
<a class="missing wiki" href="/wiki/the-departed" rel="nofollow">the-departed?</a>
</p>
"""


MAINTAINER_MACRO_TICKET_TEST_CASE = u"""
==============================
[[Maintainer]]
------------------------------
<p>
</p><div class="system-message"><strong>Maintainer macro error</strong>\
<pre>Hack name must be specified as argument when the context realm is not \'wiki\'</pre>\
</div><p>
</p>
==============================
[[Maintainer(TracHacksPlugin)]]
------------------------------
<p>
<a class="missing wiki" href="/wiki/mrenzmann" rel="nofollow">mrenzmann?</a>
</p>
==============================
[[Maintainer(FullBlogPlugin)]]
------------------------------
<p>
<a class="wiki" href="/wiki/osimons">osimons</a>
</p>
==============================
[[Maintainer(AccountManagerPlugin)]]
------------------------------
<p>
<em>Component "AccountManagerPlugin" does not exist</em>
</p>
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
    component4 = Component(tc.env)
    component4.name = 'TracMigratePlugin'
    component4.owner = 'jun66j5'
    component4.insert()
    component5 = Component(tc.env)
    component5.name = 'DeprecatedMacro'
    component5.insert()
    component6 = Component(tc.env)
    component6.name = 'DeprecatedPlugin'
    component6.owner = 'the-departed'
    component6.insert()
    ticket = Ticket(tc.env)
    ticket['summary'] = 'Ticket summary'
    ticket['reporter'] = 'hasienda'
    ticket.insert()
    with tc.env.db_transaction as db:
        TagSetup(tc.env).upgrade_environment(db)
    page1 = WikiPage(tc.env, 'osimons')
    page1.text = 'osimons'
    page1.save('osimons', '', '127.0.0.1')
    page2 = WikiPage(tc.env, 'DeprecatedMacro')
    page2.text = 'The macro is deprecated'
    page2.save('admin', '', '127.0.0.1')
    tag_resource(tc.env, page2.resource, tags=['deprecated'])
    page3 = WikiPage(tc.env, 'DeprecatedPlugin')
    page3.text = 'The plugin is deprecated'
    page3.save('the-departed', '', '127.0.0.1')
    page4 = WikiPage(tc.env, 'jun66j5')
    page4.text = 'jun66j5'
    page4.save('jun66j5', '', '127.0.0.1')
    session = DetachedSession(tc.env, 'jun66j5')
    session.set('name', 'Jun Omae')
    session.save()


def teardown(tc):
    tc.env.reset_db()
    with tc.env.db_transaction as db:
        db("DROP TABLE IF EXISTS tags")
        db("DROP TABLE IF EXISTS tags_change")
        db("DELETE FROM system WHERE name='tags_version'")


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
