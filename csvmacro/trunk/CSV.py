# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.wiki.macros import WikiMacroBase
from trac.util import escape
from StringIO import StringIO
import csv

author = "Alec Thomas"
author_email = "alec@swapoff.org"
version = "1.0-$Rev$"
license = "3-Clause BSD"
url = "https://trac-hacks.org/wiki/CsvMacro"


class CsvMacro(WikiMacroBase):
    """
    Display CSV data in a table. Simply copy and paste the CSV data
    into the macro body and hope for the best.

    Example:
    {{{
    {{{
    #!CSV
    123	123	123	123
    234	234	234	234
    }}}
    }}}
    Renders as

    || 123 || 123 || 123 || 123 ||
    || 234 || 234 || 234 || 234 ||
     """

    def get_macros(self):
        yield 'CSV'

    def expand_macro(self, formatter, name, txt):
        sniffer = csv.Sniffer()
        txt = txt.encode('ascii', 'replace')
        reader = csv.reader(StringIO(txt), sniffer.sniff(txt))
        formatter.out.write('<table class="wiki">\n')
        for row in reader:
            formatter.out.write('<tr>')
            for col in row:
                formatter.out.write('<td>%s</td>' % escape(col))
            formatter.out.write('</tr>\n')
        formatter.out.write('</table>\n')
