# -*- coding: utf-8 -*-

import unittest

from tracmigrate.tests import admin


def suite():
    suite = unittest.TestSuite()
    suite.addTest(admin.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
