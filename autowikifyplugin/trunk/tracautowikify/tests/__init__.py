#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 Jun Omae <jun66j5@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from tracautowikify.tests import autowikify


def suite():
    suite = unittest.TestSuite()
    suite.addTest(autowikify.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
