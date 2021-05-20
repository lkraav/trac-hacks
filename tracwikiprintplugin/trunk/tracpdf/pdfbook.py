# -*- coding: utf-8 -*-
# Copyright (c) 2021 Cinc
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
try:
    from ConfigParser import ConfigParser
    PY2 = True
except ImportError:
    from configparser import ConfigParser
    PY2 = False
from io import StringIO

from trac.util.html import tag
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase


def parse_makro_content(content):
    """Parse the makro contents holding the configuration for a PDF book.
    :param content: wiki text specifying the PDF book.
    :return dict with:
            {'coverpage': name of wiki page to use as cover,
             'toc': True|False - wether to add a table of contents,
             'pages': list of wiki page names
            }

    Note: see makro documentation for a description of the expected format.
    """
    config = ConfigParser(allow_no_value=True)
    config.optionxform = to_unicode
    if PY2:
        config.readfp(StringIO(content), "PdfBook")
    else:
        config.read_file(StringIO(content), "PdfBook")

    config['DEFAULT'] = {'cover': None,
                         'toc': False}
    pages = [page for page in config.options('pages') if page not in ('cover, toc')]
    data = {'coverpage': config.get('config', 'cover'),
            'toc': config.getboolean('config', 'toc'),
            'pages': pages}

    return data


class PdfBook(WikiMacroBase):
    """Create a PDF book with configuration specified in the makro contents.

    The configuration from the makro is rendered to the user and a
    button added to create a PDF book.
    Note that only one !PdfBook makro on a wiki page is supported.

    Define the makro like this:
    {{{
    {{{#!PdfBook
    [parameters]
    cover = CoverPage
    toc = 1

    [pages]
    WikiStart
    WikiFormatting
    }}}
    }}}
    Only syntax of WikiProcessors is supported.
    ==== Configuration
    The content must be formatted like an ''INI'' file. The following
    sections are supported:
    {{{#!ini
    [parameters]
    # Name of a wiki page to be used as the cover page
    cover = CoverPage
    # Set to 1 for a table of contents, else set to 0
    toc = 1

    [pages]
    # Names of wiki pages to be added to the PDF book.
    WikiStart
    WikiFormatting
    }}}
    """
    tmpl = """
Cover page:
 {coverpage}

Table of contents:
 {toc}

Pages:
 {pages}
"""
    create_button = """
{{{
#!html
<form action="%s" method="get"><div>
<input type="hidden" name="pdfbook" value="1" />
<input type="hidden" name="createbook" value="1" />
<input type="submit" value="Create PDF book"/>
</div></form>
}}}
"""

    def expand_macro(self, formatter, name, content, args=None):
        if args == None:
            return tag.div(tag.p(_("Makro PdfBook must be called as a WikiProcessor.")),
                           class_="system-message warning")
        data = parse_makro_content(content)
        pages = ''.join([' %s[[BR]]' % page for page in data['pages']])
        txt = self.tmpl.format(coverpage=data['coverpage'], pages=pages,
                               toc='Yes' if data['toc'] else 'No')
        # resource.id is the current wiki page name
        url = formatter.context.href('wikiprintpdfbook', formatter.context.resource.id)
        txt += self.create_button % url
        return format_to_html(self.env, formatter.context, txt)
