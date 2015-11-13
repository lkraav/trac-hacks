# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trachacks.tests import macros, web_ui


def test_suite():
    suite = unittest.TestSuite()

    suite.addTest(macros.test_suite())
    suite.addTest(web_ui.test_suite())

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
