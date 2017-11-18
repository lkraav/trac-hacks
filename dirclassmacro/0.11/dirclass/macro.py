# -*- coding: utf-8 -*-
#

from genshi import Markup
from trac.core import implements
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.macros import WikiMacroBase


class RTLMacro(WikiMacroBase):
    """Emits dir-aligned div blocks."""

    implements(ITemplateProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        yield 'dirclass', resource_filename(__name__, 'htdocs')

    # IWikiMacroProvier methods
    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'dirclass/css/dirclass.css')
        return Markup('<div class="rtl">')


class LTRMacro(WikiMacroBase):
    """End a dir-aligned div block."""

    def expand_macro(self, formatter, name, content):
        return Markup('</div>')
