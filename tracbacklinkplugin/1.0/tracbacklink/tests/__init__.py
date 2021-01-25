# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest


def test_suite():
    from . import api, web_ui
    suite = unittest.TestSuite()
    for module in (api, web_ui):
        suite.addTest(module.test_suite())
    return suite
