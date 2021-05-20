# -*- coding: utf-8 -*-
# Copyright (c) 2019 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import unittest
try:
    import pygments
    from pygments.formatters.html import HtmlFormatter
except ImportError:
    pygments_loaded = False
else:
    get_style_by_name = pygments.styles.get_style_by_name
    pygments_loaded = True

from trac.test import EnvironmentStub, Mock, MockRequest

from wikiprint.wikiprint import WikiPrint

class TestWikiTable(unittest.TestCase):

    @staticmethod
    def _log(*kwargs):
        try:
            msg, parm = kwargs
            print(msg % parm)
        except ValueError:
            print(kwargs[0])

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=['trac.*',
                                                             'wikiprint.*',
                                                             ])
        self.log = Mock(info=self._log, debug=self._log, error=self._log, handlers=[])
        self.env.log = self.log
        self.plugin = WikiPrint(self.env)

    def tearDown(self):
        self.env.shutdown()

    def test_table(self):
        req = MockRequest(self.env)
        table = """== Table

||= Header 1 =||= Header 2 =||
{{{#!td
  TD 1
}}}
{{{#!td
  TD 2
}}}
"""

        html_page = self.plugin.wikipage_to_html(table, 'FooPage', req)
        pdf = self.plugin.html_to_pdf(req, [html_page], False)
        self.assertIsNotNone(pdf)

    def test_broken_table(self):
        req = MockRequest(self.env)
        table = """== Broken Table

||= Header 1 =||= Header 2 =||
{{{#!td
  TD 1
}}}
{{{#!td
  TD 2
}}}
"""
        # This creates a second table with empty <tr> (no <td>)
        # There is an empty line preceeding '|--------------'
        txt = table + "\n|----------------------------------"
        html_page = self.plugin.wikipage_to_html(txt, 'FooPage', req)
        self.assertIsNotNone(self.plugin.html_to_pdf(req, [html_page], False))
        # This adds an empty <tr> to the table
        txt = table + "|----------------------------------"
        html_page = self.plugin.wikipage_to_html(txt, 'FooPage', req)
        self.assertIsNotNone(self.plugin.html_to_pdf(req, [html_page], False))


if __name__ == '__main__':
    unittest.main()
