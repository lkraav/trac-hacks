"""
TagsRequestHandler:
a plugin for Trac for autocompletion of tags
http://trac.edgewall.org
"""
from pkg_resources import resource_filename

from trac.core import *
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet

from tractags.api import TagSystem


class TagsRequestHandler(Component):

    implements(IRequestFilter, IRequestHandler)

    # IRequestHandler methods

    def match_request(self, req):
        return False

    def process_request(self, req):
        query = req.args.get('q', '').lower()
        tagsystem = TagSystem(self.env)
        alltags = tagsystem.query(req)
        tags = {}
        for resource, _tags in alltags:
            for tag in _tags:
                if query in tag.lower():
                    tags[tag] = tags.setdefault(tag, 0) + 1

        tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
        writeOut = '\n'.join('%s|%d' % (name, number) for name, number in tags)
        req.send_header('Content-length', str(len(writeOut)))
        req.end_headers()
        req.write(writeOut)

    # IRequestFilter methods

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    def pre_process_request(self, req, handler):
        if req.path_info.rstrip() == '/tags' and \
                req.args.get('format') == 'txt':
            return self
        return handler


class AutocompleteTags(Component):

    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            add_stylesheet(req, 'tags/css/autocomplete.css')
            add_script(req, 'tags/js/autocomplete.js')
            add_script(req, 'tags/js/autocomplete_keywords.js')
        return template, data, content_type

    def pre_process_request(self, req, handler):
        return handler

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('tags', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
