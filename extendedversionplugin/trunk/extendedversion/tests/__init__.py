# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest


def test_suite():
    suite = unittest.TestSuite()

    import extendedversion.tests.version
    suite.addTest(extendedversion.tests.version.test_suite())

    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python tractags/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
