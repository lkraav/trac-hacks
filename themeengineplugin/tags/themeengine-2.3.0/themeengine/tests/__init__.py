# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2020 Olemis Lang <olemis@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from themeengine.tests import api


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(api.test_suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
