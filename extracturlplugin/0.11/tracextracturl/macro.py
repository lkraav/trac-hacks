# -*- coding: utf-8 -*-
""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    v0.1 - Oct 2008
    This is Free Software under the GPL v3!
"""

from trac.core import Component, implements
from trac.util.html import html as tag
from trac.wiki.api import IWikiMacroProvider, parse_args

from extracturl import extract_url


class ExtractUrlMacro(Component):
    """Provides test macro for the `tracextracturl.extract_url` function.

This macro is intended for code testing by the developers of the above function
and has no real usage for normal Trac users.

Macro usage: `[[ExtractUrl(traclink)]]` [[BR]]
Result: The URL extracted by `extract_url`

$Id$
    """
    implements(IWikiMacroProvider)

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args(content)
        largs.append('')
        wlink = largs[0]
        raw = True
        if 'raw' in kwargs and kwargs['raw'].lower() == 'false':
            raw = False

        url = extract_url(self.env, formatter.context, wlink, raw)
        return tag.p(
            tag.code("'%s'" % wlink),
            tag.span(' => '),
            tag.a("'%s'" % url, href=url),
            class_='extracturl',
        )

    def get_macro_description(self, name):
        return self.__doc__ + "\n\n" + extract_url.__doc__

    def get_macros(self):
        yield 'ExtractUrl'
