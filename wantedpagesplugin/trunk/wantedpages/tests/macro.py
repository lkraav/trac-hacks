# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009 Justin Francis <jfrancis@justinfrancis.org>
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from trac.test import EnvironmentStub
from trac.wiki.model import WikiPage
from trac.wiki.tests import formatter

import wantedpages.macro


MACRO_TEST_CASE = u"""
==============================
[[WantedPages]]
------------------------------
<p>
<ul><li><a class="missing wiki" href="/wiki/NoSpaces" rel="nofollow">NoSpaces?</a>
</li><li><a class="missing wiki" href="/wiki/ParentWiki/SubWiki" rel="nofollow">ParentWiki/SubWiki?</a>
</li><li><a class="missing wiki" href="/wiki/TimLeo" rel="nofollow">TimLeo?</a>
</li><li><a class="missing wiki" href="/wiki/TimLowe" rel="nofollow">TimLowe?</a>
</li><li><a class="missing wiki" href="/wiki/TimLowe6" rel="nofollow">TimLowe6?</a>
</li><li><a class="missing wiki" href="/wiki/TimLowe7" rel="nofollow">TimLowe7?</a>
</li><li><a class="missing wiki" href="/wiki/WikiProcessors" rel="nofollow">WikiProcessors?</a>
</li><li><a class="missing wiki" href="/wiki/page2" rel="nofollow">page2?</a>
</li><li><a class="missing wiki" href="/wiki/pagename" rel="nofollow">pagename?</a>
</li></ul>
</p>
------------------------------
"""


CONTENT = """
== Positive test cases
 TimLowe
 TimLeo#Bio
 ParentWiki/SubWiki
NoSpaces
 [wiki:TimLowe6]
 [wiki:TimLowe7 Click here for more info]
 [wiki:pagename]
 [wiki:page2]

== Negative test cases
 TimLowe5
 !TimLewo
 {{{Timlow}}}
`TimLee`
3TimLoo
[[MyMacro]]
ParentWiki/SubWiki
[http://external external link]
http://ExternalLink
http://ExternalTrac/wiki/TomFool
{{{
<IfModule mod_fastcgi.c>
   AddHandler fastcgi-script .fcgi
   FastCgiIpcDir /var/lib/apache2/fastcgi
</IfModule>
}}}
{{{
  if (MyClass)  { return null };
}}}
[wiki:WikiProcessors TracWikiProcessor] (don't pickup the display  name even though it is camel case)
{{{
  PythonPath "sys.path + ['/path/to/trac']"
}}}
{{{
{{{
}}}
NestedBlocks
}}}
http://c2.com/cgi/wiki?WikiHistory
"""


def setUp(tc):
    tc.env = EnvironmentStub(enable=['trac.*', 'wantedpages.*'])
    page = WikiPage(tc.env)
    page.name = 'DanglingLinks'
    page.text = CONTENT
    page.save('joe', 'first edit', '::1')


def tearDown(tc):
    tc.env.reset_db()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.suite(MACRO_TEST_CASE, setUp, __file__, tearDown))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
