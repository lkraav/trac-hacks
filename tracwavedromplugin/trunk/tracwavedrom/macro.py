# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2023 Jun Omae
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import pkg_resources
import re

from trac.core import Component, implements
from trac.config import Option
from trac.web.chrome import ITemplateProvider, add_script, add_script_data
from trac.wiki.api import IWikiMacroProvider

try:
    from trac.util.html import tag
except ImportError:
    from genshi.builder import tag


class WaveDromMacro(Component):

    implements(ITemplateProvider, IWikiMacroProvider)

    wavedrom_location = Option(
        'wavedrom', 'location',
        'https://cdnjs.cloudflare.com/ajax/libs/wavedrom/3.1.0/',
        doc='Location of the !WaveDrom !JavaScript library.')

    wavedrom_skin = Option(
        'wavedrom', 'skin', 'default',
        doc='Skin of the !WaveDrom diagram.')

    # ITemplateProvider methods

    _htdocs_dirs = (
        ('wavedrom', pkg_resources.resource_filename(__name__, 'htdocs')),
    )

    def get_htdocs_dirs(self):
        return self._htdocs_dirs

    def get_templates_dirs(self):
        return ()

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'WaveDrom'
        yield 'wavedrom'

    def get_macro_description(self, name):
        return """\
!WaveDrom processor provides to render wavedrom drawings within a Trac
wiki page.

Example:
{{{
{{{
#!WaveDrom
{ "signal" : [{ "name": "Alfa", "wave": "01.zx=ud.23.45" }] }
}}}
}}}
"""

    _quote = dict(zip('&<>', map(lambda v: r'\x%02x' % ord(v), '&<>')))
    _quote_re = re.compile('[&<>]')

    def expand_macro(self, formatter, name, content):
        if content and content.strip():
            req = formatter.req
            if add_script(req, 'wavedrom/load.js') is not False:
                self._add_script_data(req)
            repl = lambda m: self._quote[m.group(0)]
            return tag.script(self._quote_re.sub(repl, content),
                              type='WaveDrom')

    # Internal methods

    def _add_script_data(self, req):
        data = {'location': self.wavedrom_location, 'skin': self.wavedrom_skin}
        add_script_data(req, {'tracwavedrom': data})
