# Copyright (c) 2008, Philippe Monnaie <philippe.monnaie@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from trac.core import TracError
from trac.util.html import html
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase


class PageVariable(WikiMacroBase):
    """
    PageVariable macro.
    This macro sets or gets a variable that is accessible throughout the
    entire page.

    Use: [[PageVariable(name,value)]]
    Name signifies the name of the parameter.
    Value signifies the value the parameter should be set to.
    If a value is supplied, this macro returns an empty string. When
    trying to set a variable that is already set (or present in the url
    for some other reason), an error is raised.

    If the parameter value is ommitted, the currently known value is
    returned. If no value is known, an error is raised.
    """

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, args):
        args = parse_args(args)[0]
        req = formatter.req
        if not hasattr(req, 'page_variables'):
            req.page_variables = {}
        if len(args) == 1:
            key = args[0]
            val = req.page_variables.get(key)
            if val is None:
                return html.code('ERROR: Variable %s not declared' % key)
            return val
        else:
            if len(args) == 2:
                key = args[0]
                val = req.page_variables.get(key)
                if val is not None:
                    return html.code('ERROR: Variable %s already set or present '
                                     'in the url' % key)
                else:
                    req.page_variables[key] = args[1]
                return ''
            else:
                return html.code('ERROR: Invalid number of arguments supplied '
                                 'to PageVariable macro: %s' % args)
