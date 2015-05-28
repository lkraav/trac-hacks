# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from coderev.tests import api


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(api.suite))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')