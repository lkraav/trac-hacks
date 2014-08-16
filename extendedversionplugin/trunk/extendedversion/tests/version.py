# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import shutil
import tempfile
import unittest

from trac.test import EnvironmentStub, Mock

from extendedversion.version import VisibleVersion


class VisibleVersionTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'extendedversion.*'],
                                   path=tempfile.mkdtemp())
        self.visible_version = VisibleVersion(self.env)

    def tearDown(self):
        shutil.rmtree(self.env.path)

    def test_match_request_a(self):
        req = Mock(path_info='/versions')
        self.assertTrue(self.visible_version.match_request(req) is None)

    def test_match_request_b(self):
        req = Mock(path_info='/version', args={})
        self.assertTrue(self.visible_version.match_request(req))
        self.assertFalse('id' in req.args)

    def test_match_request_c(self):
        req = Mock(path_info='/version/', args={})
        self.assertTrue(self.visible_version.match_request(req))
        self.assertFalse('id' in req.args)

    def test_match_request_d(self):
        req = Mock(path_info='/version/version1', args={})
        self.assertTrue(self.visible_version.match_request(req))
        self.assertEqual('version1', req.args['id'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VisibleVersionTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
