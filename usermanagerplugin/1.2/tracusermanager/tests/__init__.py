# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

import unittest

from tracusermanager.tests import api, macros_um_profile


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(api.test_suite())
    suite.addTest(macros_um_profile.test_suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
