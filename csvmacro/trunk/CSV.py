# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import csv
import io
import sys

from trac.wiki.macros import WikiMacroBase
from trac.util.html import escape

author = "Alec Thomas"
author_email = "alec@swapoff.org"
version = "1.0-$Rev$"
license = "3-Clause BSD"
url = "https://trac-hacks.org/wiki/CsvMacro"


_py2 = sys.version_info[0] == 2


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

    def expand_macro(self, formatter, name, content):
        sniffer = csv.Sniffer()
        if _py2:
            content = content.encode('utf-8')
            f = io.BytesIO(content)
        else:
            f = io.StringIO(content)
        with io.StringIO() as out:
            with f:
                reader = csv.reader(f, sniffer.sniff(content))
                out.write(u'<table class="wiki">\n')
                out.write(u'<tbody>\n')
                for row in reader:
                    out.write(u'<tr>')
                    for col in row:
                        if isinstance(col, bytes):
                            col = col.decode('utf-8')
                        out.write(u'<td>')
                        out.write(escape(col))
                        out.write(u'</td>')
                    out.write(u'</tr>\n')
                out.write(u'</tbody>\n')
                out.write(u'</table>\n')
            return out.getvalue()
