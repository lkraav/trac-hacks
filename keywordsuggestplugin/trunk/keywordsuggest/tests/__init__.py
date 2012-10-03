# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest


def test_suite():
    suite = unittest.TestSuite()
    
    import keywordsuggest.tests.web_ui
    suite.addTest(keywordsuggest.tests.web_ui.test_suite())
    
    return suite

