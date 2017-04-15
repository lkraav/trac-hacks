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

from trac.perm import PermissionCache, PermissionSystem
from trac.test import EnvironmentStub, MockRequest
from trac.util.html import html as tag
from trac.web.chrome import web_context

from tracdiscussion.util import format_to_oneliner_no_links
from tracdiscussion.util import prepare_topic, topic_status_from_list
from tracdiscussion.util import topic_status_to_list


class _BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.req = MockRequest(self.env, authname='user', method='GET')
        self.req.perm = PermissionCache(self.env, 'user')

        self.context = web_context(self.req)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)


class FormatToOnlinerNoLinksTestCase(_BaseTestCase):
    def test_format_to_oneliner_no_links(self):
        markup = tag('text-only fragment')
        self.assertEqual(format_to_oneliner_no_links(
            self.env, self.context, markup), str(markup))
        self.assertEqual(format_to_oneliner_no_links(
            self.env, self.context,
            'text fragment with [/ link]'),
            'text fragment with link')


class PrepareTopicTestCase(_BaseTestCase):
    def test(self):
        uids = (('a', '1st user', 'a@b.com'), ('b', '2nd user', 'b@d.net'))
        self.assertEqual(dict(status=set(['unsolved']),
                              subscribers=['a', 'b'],
                              unregistered_subscribers=set(['a', 'b'])),
                         prepare_topic(uids, dict(status=0,
                                                  subscribers='a b')))


class TopicStatusTestCase(_BaseTestCase):
    def test_status_from_list(self):
        self.assertEqual(0, topic_status_from_list(['unsolved']))
        self.assertEqual(0x01, topic_status_from_list(['solved']))
        self.assertEqual(0x02, topic_status_from_list(['locked']))
        self.assertEqual(0x03,
                         topic_status_from_list(['locked', 'solved']))
        # 'locked' and 'solved' are dominating.
        self.assertEqual(0x01,
                         topic_status_from_list(['solved', 'unsolved']))
        self.assertEqual(0x02,
                         topic_status_from_list(['locked', 'unsolved']))

    def test_status_to_list(self):
        self.assertEqual(set(['unsolved']), topic_status_to_list(0))
        self.assertEqual(set(['solved']), topic_status_to_list(0x01))
        self.assertEqual(set(['locked', 'unsolved']),
                         topic_status_to_list(0x02))
        self.assertEqual(set(['locked', 'solved']),
                         topic_status_to_list(0x03))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FormatToOnlinerNoLinksTestCase))
    suite.addTest(unittest.makeSuite(PrepareTopicTestCase))
    suite.addTest(unittest.makeSuite(TopicStatusTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
