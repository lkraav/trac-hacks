"""
LoomingClouds:
a plugin for Trac
http://trac.edgewall.org
"""

from collections import Counter
from pkg_resources import resource_filename

from trac.config import IntOption
from trac.core import *
from trac.util.html import html as tag
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, add_script, add_script_data, add_stylesheet, web_context)
from tractags.macros import TagSystem, TagWikiMacros
from .jtransform import JTransformer


class LoomingClouds(Component):

    implements(IRequestFilter, ITemplateProvider)

    max_keywords = IntOption('loomingclouds', 'max_keywords', doc="""
        Maximum number of keywords to display in the cloud.""")

    min_count = IntOption('loomingclouds', 'min_count', default=1, doc="""
        Hide tags with count less than this value.""")

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, metadata=None):

        if template in ('ticket.html', 'agilo_ticket_new.html',):

            tag_system = TagSystem(self.env)
            all_realms = tag_system.get_taggable_realms()
            all_tags = tag_system.get_all_tags(req, realms=all_realms)
            tags = Counter(dict(all_tags.most_common(self.max_keywords))) \
                   if self.max_keywords else all_tags

            cloud = to_unicode(TagWikiMacros(self.env).render_cloud(req, tags, caseless_sort=True,
                                                                    mincount=self.min_count,
                                                                    realms=all_realms))
            filter_list = []
            more =to_unicode(tag.a(_("More..."), href='#', title=_("Show all tags"),
                                   class_='tag-cloud-filler'))
            xform = JTransformer('.trac-properties tr:has(input#field-keywords)')
            row = '<tr><td colspan="2"></td>' \
                  '<td colspan="2"><div class="tag-cloud-div">{cloud}{more}<span class="help"> {help}</span></div></td></tr>'
            filter_list.append(xform.after(row.format(cloud=cloud, more=more,
                                                      help=_('(Click on a tag to add it. Click again to remove it.)'))))
            add_stylesheet(req, 'tags/css/tractags.css')
            add_stylesheet(req, 'loomingclouds/css/tagcloud.css')
            add_script_data(req, {'loomingclouds_filter': filter_list})
            add_script(req, 'loomingclouds/js/tag_filler.js')

        return template, data, metadata

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('loomingclouds', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
