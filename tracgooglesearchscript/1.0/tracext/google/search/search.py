# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et

import re

from genshi.filters.transform import Transformer

from trac.core import Component, implements
from trac.web import IRequestHandler
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import Chrome


class AdsenseForSearch(Component):
    config = env = log = None
    implements(ITemplateStreamFilter, IRequestHandler)

    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        if not self.config.getbool('google.search',
                                   'google_search_active', True):
            self.log.debug('Google search disabled. Returning regular stream.')
            return stream

        search_form_id = self.config.get('google.search',
                                         'search_form_id', 'search')
        forid = self.config.get('google.search', 'search_form_forid', None)
        client_id = self.config.get('google.search',
                                    'search_form_client_id', None)

        if not search_form_id:
            self.log.warn('The value of the search form id is empty. Returning '
                          'regular template stream')
            return stream
        elif not forid:
            self.log.warn('The value of "FORID" for the search form is empty. '
                          'Returning regular template stream')
            return stream
        elif not client_id:
            self.log.warn('The value of "Client ID" for the search form is '
                          'empty. Returning regular template stream')
            return stream
        template = Chrome(self.env).load_template('google_search_form.html')
        data = dict(
            req = req,
            search_form_id = search_form_id,
            input_width = self.config.get('google.search',
                                          'search_form_text_input_width', 31),
            charset = self.config.get('trac', 'default_charset', 'utf-8'),
            forid = forid,
            client_id = client_id
        )
        return stream | Transformer('//div/form[@id="%s"]' % search_form_id) \
                                    .replace(template.generate(**data))

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/gsearch/?', req.path_info) is not None

    def process_request(self, req):
        data = dict(
            iframe_initial_width = self.config.getint('google.search',
                                                      'iframe_initial_width'))
        return 'google_search_results.html', data, None
