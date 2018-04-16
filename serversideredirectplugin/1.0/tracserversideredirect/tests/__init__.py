#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 Martin Scharrer <martin@scharrer-online.de>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from tracserversideredirect.tests import plugin


def suite():
    suite = unittest.TestSuite()
    suite.addTest(plugin.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
