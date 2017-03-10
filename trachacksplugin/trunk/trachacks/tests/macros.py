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
from trac.wiki.test import wikisyntax_test_suite

import trachacks.macros
from tractags.api import TagSystem
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
<em>none (<a href="/tags/needsadoption">needsadoption</a>)</em>
</p>
==============================
[[Maintainer(TracHacksPlugin, owner)]]
------------------------------
<p>
<div class="system-message">\
<strong>Macro Maintainer(TracHacksPlugin, owner) failed</strong>\
<pre>Invalid number of arguments</pre>\
</div>
</p>
==============================
[[Maintainer(DeprecatedMacro)]]
------------------------------
<p>
<em>none (<a href="/tags/deprecated">deprecated</a>)</em>
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
<div class="system-message">\
<strong>Macro Maintainer(None) failed</strong>\
<pre>Hack name must be specified as argument when the context realm is not \'wiki\'</pre>\
</div>
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


MAINTAINER_MACRO_NEWHACK_TEST_CASE = u"""
==============================
[[Maintainer]]
------------------------------
<p>
<a class="wiki" href="/wiki/jun66j5">Jun Omae</a>
</p>
"""


def setup(tc):
    with tc.env.db_transaction as db:
        TagSetup(tc.env).upgrade_environment(db)
    tc.context.req.environ['PATH_INFO'] = '/wiki/WikiStart'
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
    page1 = WikiPage(tc.env, 'osimons')
    page1.text = 'osimons'
    page1.save('osimons', '')
    page2 = WikiPage(tc.env, 'DeprecatedMacro')
    page2.text = 'The macro is deprecated'
    page2.save('admin', '')
    tag_resource(tc.env, page2.resource, tags=['deprecated'])
    page3 = WikiPage(tc.env, 'DeprecatedPlugin')
    page3.text = 'The plugin is deprecated'
    page3.save('the-departed', '')
    page4 = WikiPage(tc.env, 'jun66j5')
    page4.text = 'jun66j5'
    page4.save('jun66j5', '')
    page5 = WikiPage(tc.env, 'MilestoneMacro')
    page5.text = 'The macro needsadoption'
    page5.save('admin', '')
    tag_resource(tc.env, page5.resource, tags=['needsadoption'])
    session = DetachedSession(tc.env, 'jun66j5')
    session.set('name', 'Jun Omae')
    session.save()


def setup_newhack(tc):
    with tc.env.db_transaction as db:
        TagSetup(tc.env).upgrade_environment(db)
    tc.context.req.environ['PATH_INFO'] ='/newhack'
    tc.context.req.authname = 'jun66j5'
    page = WikiPage(tc.env, 'jun66j5')
    page.text = 'jun66j5'
    page.save('jun66j5', '')
    session = DetachedSession(tc.env, 'jun66j5')
    session.set('name', 'Jun Omae')
    session.save()
    tc.context.req.session = session


def teardown(tc):
    tc.env.reset_db()
    with tc.env.db_transaction as db:
        db("DROP TABLE IF EXISTS tags")
        db("DROP TABLE IF EXISTS tags_change")
        db("DELETE FROM system WHERE name='tags_version'")


def test_suite():
    suite = unittest.TestSuite()
    components = ('trac.*', 'tractags.*', 'trachacks.*')
    suite.addTest(wikisyntax_test_suite(
        MAINTAINER_MACRO_WIKI_TEST_CASE, setup, __file__, teardown,
        ('wiki', 'TracHacksPlugin'), enable_components=components))
    suite.addTest(wikisyntax_test_suite(
        MAINTAINER_MACRO_TICKET_TEST_CASE, setup, __file__, teardown,
        ('ticket', 1), enable_components=components))
    suite.addTest(wikisyntax_test_suite(
        MAINTAINER_MACRO_NEWHACK_TEST_CASE, setup_newhack, __file__, teardown,
        (None, None), enable_components=components))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
