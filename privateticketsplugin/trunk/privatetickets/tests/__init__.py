# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Noah Kantrowitz
# Copyright (C) 2012-2017 Ryan J Ollos
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from privatetickets.tests import policy


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(policy.test_suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
