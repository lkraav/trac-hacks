#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest


def test_suite():
    suite = unittest.TestSuite()

    import wantedpages.tests.macro
    suite.addTest(wantedpages.tests.macro.test_suite())

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
