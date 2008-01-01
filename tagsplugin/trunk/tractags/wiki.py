from trac.core import *
from tractags.api import DefaultTagProvider, TagSystem
from trac.web.chrome import add_stylesheet
from trac.wiki.api import IWikiSyntaxProvider
from trac.resource import Resource, render_resource_link, get_resource_url
from trac.mimeview.api import Context
from trac.web.api import ITemplateStreamFilter
from trac.wiki.api import IWikiPageManipulator
from trac.util.compat import sorted
from genshi.builder import tag
from genshi.filters.transform import Transformer


class WikiTagProvider(DefaultTagProvider):
    """Tag provider for the Wiki."""
    realm = 'wiki'

    def check_permission(self, perm, operation):
        map = {'view': 'WIKI_VIEW', 'modify': 'WIKI_MODIFY'}
        return super(WikiTagProvider, self).check_permission(perm, operation) \
            and map[operation] in perm


class WikiTagInterface(Component):
    implements(ITemplateStreamFilter, IWikiPageManipulator)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        page_name = req.args.get('page', 'WikiStart')
        resource = Resource('wiki', page_name)
        if filename == 'wiki_view.html' and 'TAGS_VIEW' in req.perm(resource):
            return self._wiki_view(req, stream)
        elif filename == 'wiki_edit.html' and 'TAGS_MODIFY' in req.perm(resource):
            return self._wiki_edit(req, stream)
        return stream

    # IWikiPageManipulator methods
    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        if req and 'TAGS_MODIFY' in req.perm(page.resource) \
                and req.path_info.startswith('/wiki') and 'save' in req.args:
            if self._update_tags(req, page) and \
                    page.text == req.args.get('text') and \
                    page.readonly == int('readonly' in req.args):
                req.redirect(get_resource_url(self.env, page.resource, req.href, version=None))
        return []

    # Internal methods
    def _page_tags(self, req):
        pagename = req.args.get('page', 'WikiStart')

        tag_system = TagSystem(self.env)
        resource = Resource('wiki', pagename)
        tags = sorted(tag_system.get_tags(req, resource))
        return tags

    def _wiki_view(self, req, stream):
        tags = self._page_tags(req)
        if not tags:
            return stream
        tag_system = TagSystem(self.env)
        add_stylesheet(req, 'tags/css/tractags.css')
        li = []
        for tag_ in tags:
            resource = Resource('tag', tag_)
            anchor = render_resource_link(self.env,
                Context.from_request(req, resource), resource)
            li.append(tag.li(anchor, ' '))

        insert = tag.ul(class_='tags')(tag.lh('Tags'), li)
        return stream | Transformer('//div[@class="buttons"]').before(insert)

    def _update_tags(self, req, page):
        tag_system = TagSystem(self.env)
        newtags = tag_system.split_into_tags(req.args.get('tags', ''))
        oldtags = tag_system.get_tags(req, page.resource)

        if oldtags != newtags:
            tag_system.set_tags(req, page.resource, newtags)
            return True
        return False

    def _wiki_edit(self, req, stream):
        insert = tag.div(class_='field')(
            tag.label(
                'Tag under: (', tag.a('view all tags', href=req.href.tags()), ')',
                tag.br(),
                tag.input(id='tags', type='text', name='tags', size='30',
                          value=req.args.get('tags', ' '.join(self._page_tags(req)))),
                )
            )
        return stream | Transformer('//div[@id="changeinfo1"]').append(insert)


class TagWikiSyntaxProvider(Component):
    """Provide tag:<expr> links."""

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        yield (r'''\[tag(?:ged)?:(?P<tlpexpr>(?:'.*?'|".*?"|\S)+)\s+(?P<tlptitle>.*?]*)\]''',
               lambda f, n, m: self._format_tagged(f,
                                    m.group('tlpexpr'),
                                    m.group('tlptitle')))
        yield (r'''tag(?:ged)?:(?P<texpr>(?:'.*?'|".*?"|\S)+)''',
               lambda f, n, m: self._format_tagged(f,
                                    m.group('texpr'),
                                    'tagged:' + m.group('texpr')))

    def get_link_resolvers(self):
        return []

    def _format_tagged(self, formatter, target, label):
        if label:
            href = formatter.context.href
            if target[0] in '\'"':
                q = target.strip('\'"')
                target = None
            else:
                q = None
            url = get_resource_url(
                self.env, Resource('tag', target),
                formatter.context.href
                )
            return tag.a(label, href=href(url, q=q))
        return render_resource_link(self.env, formatter.context,
                                    Resource('tag', target))

