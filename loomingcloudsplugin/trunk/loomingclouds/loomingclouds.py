"""
LoomingClouds:
a plugin for Trac
http://trac.edgewall.org
"""

from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from trac.core import *
from trac.util.html import html as tag
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import (
    ITemplateProvider, add_script, add_stylesheet, web_context)
from trac.wiki.formatter import Formatter

from tractags.macros import TagWikiMacros


class LoomingClouds(Component):

    implements(ITemplateProvider, ITemplateStreamFilter)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename in ('ticket.html', 'agilo_ticket_new.html',):

            add_stylesheet(req, 'tags/css/tractags.css')
            add_stylesheet(req, 'loomingclouds/css/tagcloud.css')
            add_script(req, 'loomingclouds/js/tag_filler.js')
            formatter = Formatter(self.env, web_context(req))
            macro = TagWikiMacros(self.env)
            cloud = macro.expand_macro(formatter, 'TagCloud', '')

            stream |= Transformer("//input[@id='field-keywords']").after(cloud).after(tag.a('More...',href='#',class_='tag-cloud-filler'))

        return stream

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('loomingclouds', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
