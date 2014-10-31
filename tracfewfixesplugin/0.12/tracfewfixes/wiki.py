# -*- coding: utf-8 -*-

from genshi.core import Markup

from trac.core import Component, implements
from trac.util.presentation import to_json
from trac.web.api import IRequestFilter, RequestDone
from trac.wiki.web_api import WikiRenderer


class WikiFixesComponents(Component):

    implements(IRequestFilter)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if data is not None and template == 'wiki_edit.html':
            rows = data.get('edit_rows')
            if not isinstance(rows, basestring):
                data['edit_rows'] = str(rows or 20)
        return template, data, content_type


class WikiRendererFixesFilter(Component):

    implements(IRequestFilter)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if handler is WikiRenderer(self.env):
            return self
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # faked IRequestHandler methods

    def process_request(self, req):
        fake = FakeRequest(req)
        try:
            return WikiRenderer(self.env).process_request(fake)
        except RequestDone:
            if fake.status == 200 and fake.content is not None:
                links = req.chrome.get('links', {}).get('stylesheet')
                if links:
                    script = self._load_stylesheet_script(req, links)
                    fake.content += script.encode('utf-8')
            req.send(fake.content, fake.content_type, fake.status)

    def _load_stylesheet_script(self, req, links):
        def script(link):
            href = to_json(link['href'])
            type = to_json(link['type'])
            return 'jQuery.loadStyleSheet(%s, %s);' % (href, type)
        return Markup('<script type="text/javascript">' +
                      '\n'.join(script(link) for link in links) + \
                      '</script>')


class FakeRequest(object):

    def __init__(self, req):
        self.req = req
        self.status = None
        self.content = None
        self.content_type = None

    def __getattr__(self, name):
        if name == 'send':
            return self.send
        return getattr(self.req, name)

    def __setitem__(self, name, value):
        setattr(self.req, name, value)

    def send(self, content, content_type='text/html', status=200):
        self.content = content
        self.content_type = content_type
        self.status = status
        raise RequestDone
