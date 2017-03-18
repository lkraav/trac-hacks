# -*- coding: utf-8 -*-

from trac.core import *
from trac.util.html import html
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.wiki.macros import WikiMacroBase


class SpoilerMacro(WikiMacroBase):
    """A macro to add spoilers to a page.
    """
    implements(ITemplateProvider)

    #REHIDE SPOILER WHEN CLICKING ON SPOILER TEXT... set the text background to some "spoiler color"

    def expand_macro(self, formatter, name, content, args):
        add_stylesheet(formatter.req, 'spoiler/css/spoiler.css')
        add_script(formatter.req, 'spoiler/js/spoiler.js')
        if '\n' in content:
            output = html.div(class_="spoiler") \
                     (format_to_html(self.env, formatter.context, content))
        else:
            output = html.span(class_="spoiler") \
                     (format_to_oneliner(self.env, formatter.context, content))
        return output

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('spoiler', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
