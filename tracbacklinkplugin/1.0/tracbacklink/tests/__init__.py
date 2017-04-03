# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest


def test_suite():
    from tracbacklink.tests import api
    suite = unittest.TestSuite()
    for module in [api]:
        suite.addTest(module.test_suite())
    return suite
