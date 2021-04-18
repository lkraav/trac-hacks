"""
LoomingClouds:
a plugin for Trac
http://trac.edgewall.org
"""

from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from trac.config import IntOption
from trac.core import *
from trac.util.html import html as tag
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import (
    ITemplateProvider, add_script, add_stylesheet, web_context)

from tractags.api import Counter
from tractags.macros import TagSystem, TagWikiMacros


class LoomingClouds(Component):

    implements(ITemplateProvider, ITemplateStreamFilter)

    max_keywords = IntOption('loomingclouds', 'max_keywords', doc="""
        Maximum number of keywords to display in the cloud.""")

    min_count = IntOption('loomingclouds', 'min_count', default=1, doc="""
        Hide tags with count less than this value.""")

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename in ('ticket.html', 'agilo_ticket_new.html',):

            tag_system = TagSystem(self.env)
            all_realms = tag_system.get_taggable_realms()
            all_tags = tag_system.get_all_tags(req, realms=all_realms)
            tags = Counter(dict(all_tags.most_common(self.max_keywords))) \
                   if self.max_keywords else all_tags

            cloud = TagWikiMacros(self.env).render_cloud(
                    req, tags, caseless_sort=True, mincount=self.min_count,
                    realms=all_realms)

            add_stylesheet(req, 'tags/css/tractags.css')
            add_stylesheet(req, 'loomingclouds/css/tagcloud.css')
            add_script(req, 'loomingclouds/js/tag_filler.js')

            stream |= Transformer("//input[@id='field-keywords']").after(cloud).after(tag.a('More...',href='#',class_='tag-cloud-filler'))

        return stream

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('loomingclouds', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
