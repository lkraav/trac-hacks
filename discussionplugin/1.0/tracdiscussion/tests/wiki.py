# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from StringIO import StringIO

try:
    from babel import Locale
    locale_en = Locale.parse('en_US')
except ImportError:
    Locale = None
    locale_en = None

from trac.attachment import Attachment
from trac.db.api import DatabaseManager
from trac.mimeview import Context
from trac.resource import ResourceNotFound
from trac.test import EnvironmentStub, Mock, MockPerm
from trac.util.datefmt import utc
from trac.web.href import Href
from trac.wiki.formatter import format_to_html

from tracdiscussion.init import DiscussionInit
from tracdiscussion.tests import formatter
from tracdiscussion.tests.test import insert_test_data
from tracdiscussion.wiki import DiscussionWiki


TEST_CASES = u"""
============================== discussion link resolvers
forum:1
last-forum:0
topic:2
last-topic:1
message:3
topic-attachment:3:foo.txt
raw-topic-attachment:3:foo.txt
------------------------------
<p>
<a href="/discussion/forum/1" title="forum-subject1">forum:1</a>
<a href="/discussion/forum/1" title="forum-subject1">last-forum:0</a>
<a href="/discussion/topic/2#-1" title="forum-subject1: top2">topic:2</a>
<a href="/discussion/topic/2#-1" title="forum-subject1: top2">last-topic:1</a>
<a href="/discussion/topic/2#message_3" title="forum-subject1: \
top2">message:3</a>
<p>
<a class="attachment" href="/attachment/discussion/topic/3/foo.txt" \
title="Attachment 'foo.txt' in Topic #3">topic-attachment:3:foo.txt</a><a \
class="trac-rawlink" href="/raw-attachment/discussion/topic/3/foo.txt" \
title="Download"></a>
</p>

<p>
<a class="attachment" href="/raw-attachment/discussion/topic/3/foo.txt" \
title="Attachment 'foo.txt' in Topic #3">raw-topic-attachment:3:foo.txt</a>
</p>

</p>
------------------------------
============================== invalid discussion links
forum:name
last-forum:-1
topic:'invalid'
last-topic:
message:
raw-topic-attachment:foo:bar.txt
------------------------------
<p>
<a class="missing" href="/discussion/forum/-1" \
title="forum:name">forum:name</a>
last-forum:-1
<a class="missing" href="/discussion/topic/-1" \
title="topic:'invalid'">topic:'invalid'</a>
last-topic:
message:
<p>
<a class="missing attachment">raw-topic-attachment:foo:bar.txt</a>
</p>

</p>
------------------------------
============================== missing discussion links
forum:3
last-forum:2
topic:4
last-topic:3
message:6
topic-attachment:5:bar.txt
raw-topic-attachment:5:bar.txt
------------------------------
<p>
<a class="missing" href="/discussion/forum/3" title="forum:3">forum:3</a>
<a class="missing" href="/discussion/forum/-1" \
title="last-forum:2">last-forum:2</a>
<a class="missing" href="/discussion/topic/4" title="topic:4">topic:4</a>
<a class="missing" href="/discussion/topic/-1" \
title="last-topic:3">last-topic:3</a>
<a class="missing" href="/discussion/message/6" \
title="message:6">message:6</a>
<p>
<a class="missing attachment">topic-attachment:5:bar.txt</a>
</p>

<p>
<a class="missing attachment">raw-topic-attachment:5:bar.txt</a>
</p>

</p>
------------------------------
"""


class DiscussionWikiTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.db = self.env.get_db_cnx()
        # Accomplish Discussion db schema setup.
        setup = DiscussionInit(self.env)
        setup.upgrade_environment(self.db)
        insert_test_data(self.db)

        self.wiki = DiscussionWiki(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Tests

    def test_get_macros(self):
        self.assertTrue(set(self.wiki.get_macros()),
                        set(['RecentTopics', 'ViewTopic']))

    def test_invalid_attachment_link(self):
        req = Mock(href=Href('/'), abs_href=Href('http://www.example.com/'),
                   authname='anonymous', perm=MockPerm(), tz=utc, args={},
                   locale=locale_en)
        context = Context.from_request(req)
        self.assertRaises(ResourceNotFound, format_to_html, self.env,
                          context, 'topic-attachment:foo.txt')


def wiki_setup(tc):
    tc.env = EnvironmentStub(default_data=True,
                             enable=['trac.*', 'tracdiscussion.*'])
    tc.env.path = tempfile.mkdtemp()
    tc.db_mgr = DatabaseManager(tc.env)
    tc.db = tc.env.get_db_cnx()

    # Accomplish Discussion db schema setup.
    setup = DiscussionInit(tc.env)
    setup.upgrade_environment(tc.db)
    insert_test_data(tc.db)

    attachment = Attachment(tc.env, 'discussion', 'topic/3')
    attachment.insert('foo.txt', StringIO(''), 0, 1)

    req = Mock(href=Href('/'), abs_href=Href('http://www.example.com/'),
               authname='anonymous', perm=MockPerm(), tz=utc, args={},
               locale=locale_en)
    tc.env.href = req.href
    tc.env.abs_href = req.abs_href
    tc.context = Context.from_request(req)
    # Enable big diff output.
    tc.maxDiff = None


def wiki_teardown(tc):
    tc.env.reset_db()
    tc.db.close()
    # Really close db connections.
    tc.env.shutdown()
    shutil.rmtree(tc.env.path)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionWikiTestCase, 'test'))
    suite.addTest(formatter.suite(TEST_CASES, wiki_setup, __file__,
                                  wiki_teardown))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
