# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 Jun Omae <jun66j5@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import functools
import unittest

from trac.test import EnvironmentStub, Mock, MockPerm
from trac.web.chrome import web_context
from trac.web.href import Href
from trac.wiki.formatter import format_to_oneliner
from trac.wiki.model import WikiPage

from tracacronyms.acronyms import Acronyms


class AcronymsTestCase(unittest.TestCase):

    acronym_definitions = """
||'''Acronym'''||'''Description'''            ||'''URL'''                    ||'''ID URL'''                      ||
||RFC          ||Request For Comment $1       ||http://www.ietf.org/rfc.html ||http://www.ietf.org/rfc/rfc$1.txt ||
||RFC2316      ||Request For Comment 2316     ||Rfc2316                      ||                                  ||
||URL          ||Universal Resource Locater   ||http://www.w3.org/Addressing ||   ||
||SCSI         ||Small Computer Interface Bus ||                             ||   ||
||ROM          ||Read-Only Memory             ||                             ||   ||
    """

    def setUp(self):
        self.env = EnvironmentStub(enable=[Acronyms])
        page = WikiPage(self.env)
        page.name = 'AcronymDefinitions'
        page.text = self.acronym_definitions
        page.save('admin', 'Acronyms definitions')

    def tearDown(self):
        self.env.reset_db()

    def test_definitions(self):
        req = Mock(authname='anonymous', perm=MockPerm(), tz=None, args={},
                   href=Href('/'), abs_href=Href('http://www.example.com/'))
        ctxt = web_context(req)
        format_ = functools.partial(format_to_oneliner, self.env, ctxt)
        self.assertEqual('<a class="acronym" '
                         'href="http://www.ietf.org/rfc.html">'
                         '<acronym title="Request For Comment">RFC'
                         '</acronym></a>', format_('RFC'))
        self.assertEqual('<acronym title="Small Computer Interface Bus">'
                         'SCSI</acronym>', format_("SCSI"))
        self.assertEqual('<acronym title="Read-Only Memory">ROM</acronym>',
                         format_('ROM'))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AcronymsTestCase, 'test'))
    return suite
