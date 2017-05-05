# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import pkg_resources

from trac.core import implements
from trac.ticket.api import TicketSystem
from trac.ticket.query import QueryModule
from trac.util import lazy
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_script_data


class TracFlexibleQueryUiModule(QueryModule):

    implements(IRequestFilter, IRequestHandler, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if req.method == 'GET' and req.path_info == '/query' and \
                'update' not in req.args and not req.args.getfirst('format'):
            return self
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template and req.method == 'GET' and req.path_info == '/query' and \
                hasattr(req, '_flexible_queryui'):
            self._restore_col_args(req, data)
            self._init_script(req, data)
        return template, data, content_type

    # IRequestHandler methods

    def match_request(self, req):
        return False

    def process_request(self, req):
        return QueryModule.process_request(self, req)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return iter(self._htdocs_dirs)

    def get_templates_dirs(self):
        return ()

    # Internal methods

    def display_html(self, req, query):
        cols = query.cols
        new_cols = cols[:]
        cols_set = set(new_cols)
        added_cols = set()
        for field in TicketSystem(self.env).fields:
            name = field['name']
            if name != 'id' and field['type'] != 'textarea' and \
                    name not in cols_set:
                new_cols.append(name)
                added_cols.add(name)
        query.cols = new_cols
        req._flexible_queryui = {'cols': cols}
        return QueryModule.display_html(self, req, query)

    @lazy
    def _htdocs_dirs(self):
        htdocs = pkg_resources.resource_filename(__name__, 'htdocs')
        return [('tracflexiblequeryui', htdocs)]

    def _restore_col_args(self, req, data):
        query = data['query']
        data['col'] = query.cols = req._flexible_queryui['cols']

        col_args = [arg for arg in query.get_href(req.href).split('?', 1)[1]
                                                           .split('&')
                        if arg.startswith('col=')]

        def replace_cols(url):
            pos = url.find('?')
            if pos == -1:
                return url
            args = [arg for arg in url[pos + 1:].split('&')
                        if not arg.startswith('col=')]
            args.extend(col_args)
            return url[:pos] + '?' + '&'.join(args)

        req.session['query_href'] = replace_cols(req.session['query_href'])
        links = req.chrome.get('links', {})
        for rel in ('alternate', 'next', 'prev'):
            for link in links.get(rel, []):
                link['href'] = replace_cols(link['href'])
        for page in data['paginator'].shown_pages:
            page['href'] = replace_cols(page['href'])
        for header in data['headers']:
            header['href'] = replace_cols(header['href'])

    def _init_script(self, req, data):
        col = set(data['col'])
        seen = set(['id'])
        columns = []
        columns.extend(h['name'] for h in data['headers'])
        columns.extend(data['all_columns'])
        fields = []
        for name in columns:
            if name not in seen:
                fields.append({'name': name, 'enabled': name in col})
                seen.add(name)
        add_script_data(req, {'tracflexiblequeryui': {'fields': fields}})
        add_script(req, 'tracflexiblequeryui/init.js')
