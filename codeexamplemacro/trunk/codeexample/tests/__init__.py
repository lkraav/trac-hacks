#!/usr/bin/env python

import unittest

from codeexample.tests import test_all


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_all.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
