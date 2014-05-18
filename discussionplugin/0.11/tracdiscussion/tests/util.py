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

from genshi.builder import tag

from trac.mimeview import Context
from trac.perm import PermissionCache, PermissionSystem
from trac.test import EnvironmentStub, Mock

from tracdiscussion.util import as_list, format_to_oneliner_no_links
from tracdiscussion.util import prepare_topic, topic_status_from_list
from tracdiscussion.util import topic_status_to_list


class _BaseTestCase(unittest.TestCase):
	
    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)

        self.req = Mock(authname='user', method='GET',
                   args=dict(), abs_href=self.env.abs_href,
                   chrome=dict(notices=[], warnings=[]),
                   href=self.env.abs_href, locale='',
                   redirect=lambda x: None, session=dict(), tz=''
        )
        self.req.perm = PermissionCache(self.env, 'user')

        self.context = Context.from_request(self.req)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)


class AsListTestCase(_BaseTestCase):

    def test_iterable(self):
        self.assertEqual(['1', '2', '3'], as_list('1 2 3'))
        self.assertEqual([], as_list(None))
        self.assertEqual([], as_list([]))

    def test_undefined(self):
        self.assertRaises(NotImplementedError, as_list, [1])
        self.assertRaises(NotImplementedError, as_list, self)


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
        _BaseTestCase.setUp(self)
        self.context.users = (('a', '1st user', 'a@b.com'),
                              ('b', '2nd user', 'b@d.net'))
        self.assertEqual(dict(status=set(['unsolved']),
                              subscribers=['a', 'b'],
                              unregistered_subscribers=set(['a', 'b'])),
                         prepare_topic(self.context, dict(status=0,
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
    suite.addTest(unittest.makeSuite(AsListTestCase, 'test'))
    suite.addTest(unittest.makeSuite(FormatToOnlinerNoLinksTestCase, 'test'))
    suite.addTest(unittest.makeSuite(PrepareTopicTestCase, 'test'))
    suite.addTest(unittest.makeSuite(TopicStatusTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
