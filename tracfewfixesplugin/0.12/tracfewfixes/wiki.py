# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.web.api import IRequestFilter


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
