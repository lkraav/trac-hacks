#!/usr/bin/env python
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
</p><table class="wiki">
<tr><td>Missing link
</td></tr><tr><td><a class="missing wiki" href="/wiki/TimLowe" rel="nofollow">TimLowe</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/TimLowe#Bio" rel="nofollow">TimLowe#Bio</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/UpgradeEnvironment" rel="nofollow">UpgradeEnvironment</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/ParentWiki/ChildWiki" rel="nofollow">ParentWiki/ChildWiki</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/ParentWiki" rel="nofollow">ParentWiki</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/WantedLinksTestPage/SubWiki/SubberWiki/SubbestWiki" rel="nofollow">WantedLinksTestPage/SubWiki/SubberWiki/SubbestWiki</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/WantedLinksTestPage/TubWiki/TubberWiki" rel="nofollow">WantedLinksTestPage/TubWiki/TubberWiki</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/WantedLinksTestPage/VubWiki" rel="nofollow">WantedLinksTestPage/VubWiki</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/WantedLinksTestPage/SubWiki" rel="nofollow">WantedLinksTestPage/SubWiki</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/WantedLinksTestPage/SubWiki/SubberWiki" rel="nofollow">WantedLinksTestPage/SubWiki/SubberWiki</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/Wiki_page" rel="nofollow">Wiki_page</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/Wiki_page2" rel="nofollow">Wiki_page2</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/ISO9000" rel="nofollow">ISO9000</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/ISO9001" rel="nofollow">ISO9001</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/Space%20Matters" rel="nofollow">Space Matters</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/Space%20Flatters" rel="nofollow">Space Flatters</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/WikiPageName" rel="nofollow">WikiPageName</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/some%20page%201" rel="nofollow">some page 1</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/some%20page%202" rel="nofollow">some page 2</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/alsoAWikiPage" rel="nofollow">alsoAWikiPage</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/also-a-wiki-page" rel="nofollow">also-a-wiki-page</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/some%20page%203" rel="nofollow">some page 3</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/some%20page%204" rel="nofollow">some page 4</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/XantedLinksTestPage?format=txt" rel="nofollow">XantedLinksTestPage?format=txt</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/XantedLinksTestPage?version=1" rel="nofollow">XantedLinksTestPage?version=1</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/WikiCreole%20link%20style" rel="nofollow">WikiCreole link style</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/NonExistingMacro" rel="nofollow">NonExistingMacro</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/NonExistingMacro(MyMacroParam)" rel="nofollow">NonExistingMacro(MyMacroParam)</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/XantedLinksTestPage" rel="nofollow">XantedLinksTestPage</a>
</td></tr><tr><td><a class="missing wiki" href="/wiki/CoinCoin" rel="nofollow">CoinCoin</a>
</td></tr></table>
<p>
</p>
------------------------------
"""


CONTENT = """
== Key for test cases
== WP:report as Wanted Page; IL: Ignore Link (good link or not a wiki link)

== Camelcase test cases
WP TimLowe               missing page
WP TimLowe#Bio           anchor on missing page
WP = Upgrade Environment = #UpgradeEnvironment    missing anchor
IL TimLowe5              not Camelcase because of number
IL !TimLowe              ignore links starting with !
IL {{{TimLowe}}}         inline block
IL `TimLee`              inline block
IL 3TimLowe              not Camelcase because of number
WP ParentWiki/ChildWiki    missing sub page AND missing parent page
IL ParentWiki/ChildWiki1   not Camelcase because of number
IL ParentWiki1/ChildWiki   not Camelcase because of number
IL ParentWiki1/ChildWiki1  not Camelcase because of number
IL ParentWiki/Child2Wiki   not Camelcase because of number
IL ParentWiki/Child_Wiki   not Camelcase because of underscore
WP ./SubWiki/SubberWiki/SubbestWiki    missing relative page
WP ./TubWiki/TubberWiki                missing relative page
WP ./VubWiki                           missing relative page
IL ./SubWiki7/SubberWiki/SubbestWiki   not Camelcase because of number
IL ./SubWiki/SubberWiki7/SubbestWiki   not Camelcase because of number
IL ./SubWiki/SubberWiki/SubbestWiki7   not Camelcase because of number

== Wiki syntax test cases for non-existing pages
WP [wiki:Wiki_page]                    explicit reference
WP [wiki:Wiki_page2]                   explicit reference, despite number
WP [wiki:ISO9000]                      explicit reference
WP [wiki:ISO9001 ISO 9001 standard]    explicit reference
WP [wiki:"Space Matters"]              explicit reference
WP [wiki:"Space Flatters" all about white space]  explicit reference
WP ["WikiPageName"]                    implicit reference
WP [WikiPageName]                      implicit reference
IL [WikiPageName2]                     not Camelcase because of number
IL [wikipagename]                      not Camelcase

== Wiki syntax, checking quotes and no square brackets
WP wiki:'some page 1'
WP wiki:"some page 2"
WP wiki:alsoAWikiPage
WP wiki:also-a-wiki-page
WP [wiki:'some page 3']
WP [wiki:"some page 4"]

== Ignore (wiki page) attachments ==
IL attachment:wiki:MyPage:the_file.txt

== Also check some existing pages:
IL wiki:WantedLinksTestPage?format=txt existing page
WP wiki:XantedLinksTestPage?format=txt non-existing page
IL wiki:WantedLinksTestPage?version=1  existing page
WP wiki:XantedLinksTestPage?version=1  non-existing page

== Wiki Creole syntax test cases:
WP [[WikiCreole link style]]
WP [[WikiCreole link style|WikiCreole style links]]
WP [[NonExistingMacro]]                 interpreted as Creole link
WP [[NonExistingMacro(MyMacroParam)]]   interpreted as Creole link

== External Pages, ignore all:
IL [[trac:any_page_in_trac]] ignore external pages
IL [trac:any_page_in_trac]
IL trac:any_page_in_trac
IL [[http://external external link]]
IL [http://external external link]
IL http://external external link
IL http://ExternalLink
IL http://ExternalTrac/wiki/TomFool
IL [[https://external external link]]
IL [https://external external link]
IL https://external external link
IL https://ExternalLink
IL https://ExternalTrac/wiki/TomFool
IL http://c2.com/cgi/wiki?WikiHistory   ignore Camelcase parameter

== Ignore Camelcase display names:
IL/IL [wiki:WantedLinksTestPage WantedLinksTestPage] existing page
WP/IL [wiki:XantedLinksTestPage XantedLinksTestPage] non-existing page

== Ignore !InterMapText and !InterTrac syntax ==
IL CoinCoin:wiki     !InterMapText
WP CoinCoin          not !InterMapText
IL #T234             !InterTrac
IL [trac 1508]       !InterTrac

== Complex paths ==
WP this/is/a/valid/wiki/link

== Ignore everything inside (nested) blocks:
{{{
<IfModule mod_fastcgi.c>
   AddHandler fastcgi-script .fcgi
   FastCgiIpcDir /var/lib/apache2/fastcgi
</IfModule>

if (MyClass)  { return null };

PythonPath "sys.path + ['/path/to/trac']"

CamelCaseInBlockIgnored

{{{
CamelCaseInNestedBlockIgnored
}}}

}}}
"""

def setUp(tc):
    tc.env = EnvironmentStub(enable=['trac.*', 'wantedpages.*'])
    page = WikiPage(tc.env)
    page.name = 'WantedLinksTestPage'
    page.text = CONTENT
    page.save('joe', 'first edit')


def tearDown(tc):
    tc.env.reset_db()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.test_suite(MACRO_TEST_CASE, setUp, __file__, tearDown))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
