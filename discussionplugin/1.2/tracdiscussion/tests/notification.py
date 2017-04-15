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

from trac.test import EnvironmentStub

from tracdiscussion.notification import DiscussionNotifyEmail
from tracdiscussion.notification import DiscussionEmailNotification


class DiscussionEmailNotificationTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()

        self.tag_den = DiscussionEmailNotification(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_init(self):
        pass


class DiscussionNotifyEmailTestCase(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()

        self.tag_dne = DiscussionNotifyEmail(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_init(self):
        pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionEmailNotificationTestCase))
    suite.addTest(unittest.makeSuite(DiscussionNotifyEmailTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
