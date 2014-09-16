# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest


def suite():
    print "Starting COMPLETE test suite for logwatcher"

    from logwatcher.tests import api
    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
