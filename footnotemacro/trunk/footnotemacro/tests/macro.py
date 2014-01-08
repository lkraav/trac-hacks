# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

from trac.test import EnvironmentStub
from trac.wiki.tests import formatter

import footnotemacro.macro


MACRO_TEST_CASE = u"""
==============================
This is the [[FootNote(first footnote)]].[[BR]]
This is the [[FootNote(second footnote)]].
[[FootNote]]
------------------------------
<p>
This is the <sup class="footnote"><a href="#FootNote1" id="FootNoteRef1" title="first footnote">1</a></sup>.<br />
This is the <sup class="footnote"><a href="#FootNote2" id="FootNoteRef2" title="second footnote">2</a></sup>.
</p><div class="footnotes"><hr /><ol><li id="FootNote1"><a class="sigil" href="#FootNoteRef1">1.</a> first footnote</li><li id="FootNote2"><a class="sigil" href="#FootNoteRef2">2.</a> second footnote</li></ol></div><p>
</p>
------------------------------
"""


def setUp(tc):
    tc.env = EnvironmentStub(enable=['trac.*', 'footnotemacro.*'])
    tc.context.req.chrome = {}


def tearDown(tc):
    tc.env.reset_db()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(formatter.suite(MACRO_TEST_CASE, setUp, __file__, tearDown))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
