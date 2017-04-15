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

from tracdiscussion.spamfilter import DiscussionSpamFilter


class DiscussionSpamFilterTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tracdiscussion.*'])
        self.env.path = tempfile.mkdtemp()

        self.filter = DiscussionSpamFilter(self.env)

    def tearDown(self):
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def test_init(self):
        pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DiscussionSpamFilterTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
