# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012-2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from tracpaste.tests import db, web_ui, wikisyntax


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(db.suite))
    suite.addTest(unittest.makeSuite(wikisyntax.suite))
    suite.addTest(unittest.makeSuite(web_ui.suite))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
