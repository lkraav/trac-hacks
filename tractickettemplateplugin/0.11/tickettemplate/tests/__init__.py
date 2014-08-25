# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from tickettemplate.tests import test_tt


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_tt.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
