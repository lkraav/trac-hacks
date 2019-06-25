"""
MediaWiki-style markup
parse(text) -- returns safe-html from wiki markup
code based off of mediawiki
"""

from trac.core import *
from trac.wiki.api import IWikiMacroProvider

import parser


class MediaWikiRenderer(Component):
    """
    Renders plain text in MediaWiki format as HTML
    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        """Return a list of provided macros"""
        yield 'mediawiki'

    def get_macro_description(self, name):
        return '''desc'''

    def expand_macro(self, formatter, name, content):
        if name == 'mediawiki':
            return parser.parse(content)

