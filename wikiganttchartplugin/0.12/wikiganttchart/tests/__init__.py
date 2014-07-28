# -*- coding:utf-8
#
# Copyright (C) 2014 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest


def suite():
    from wikiganttchart.tests import web_ui
    suite = unittest.TestSuite()
    suite.addTest(web_ui.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
