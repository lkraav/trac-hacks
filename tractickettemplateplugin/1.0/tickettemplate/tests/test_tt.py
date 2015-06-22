# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.core import *
from trac.test import EnvironmentStub, Mock

import tickettemplate.ttadmin as ttadmin


class TicketTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub()
        self.tt = ttadmin.TicketTemplateModule(self.env)
        self.tt.upgrade_environment()

    def tearDown(self):
        self.env.shutdown()  # really closes the db connections

    def test_match_request(self):
        req = Mock(path_info='/tt')
        self.assertEqual(True, self.tt.match_request(req))

        req = Mock(path_info='/something')
        self.assertEqual(False, self.tt.match_request(req))

    def test_loadSaveTemplateText(self):
        for tt_name, tt_text in [("default", "default text"),
                                ("defect", "defect text"),
                                ("enhancement", "enhancement text"),
                                ("task", "task text"),
                                ]:
            self.tt._saveTemplateText(tt_name, tt_text)
            self.assertEqual(tt_name + " text", self.tt._loadTemplateText(tt_name))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TicketTemplateTestCase, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main()
