# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from tracticketfieldslayout.tests import admin
from tracticketfieldslayout.tests import web_ui


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(admin.test_suite())
    suite.addTest(web_ui.test_suite())
    return suite


if __name__ == '__main__':
    unittest.main()
