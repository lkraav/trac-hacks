#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013,2017,2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
# from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
# from trac.ticket.web_ui import TicketModule
from trac.web.api import IRequestHandler, IRequestFilter
from trac.config import ListOption, IntOption
# from trac.util import Ranges, as_int
# from trac.util.html import Element
# from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage
from datetime import datetime
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script,\
    add_script_data
from pkg_resources import resource_filename

try:
    import json
except:
    from tracrpc.json_rpc import json

class TicketLinkDecorator(Component):
    """ set css-class to ticket link as ticket field value. field name can
    set in [ticket]-decorate_fields in trac.ini
    """
    implements(IRequestHandler, IRequestFilter, ITemplateProvider)

    decorate_fields = ListOption('ticket', 'decorate_fields', default='type',
        doc=""" comma separated List of field names to add css class of ticket link.
            (Provided by !ContextChrome.!TicketLinkDecorator) """)

    # IRequestHandler Methods
    def match_request(self, req):
        return req.path_info == '/contextchrome/ticketlink.jsonrpc'

    def process_request(self, req):
        payload = json.load(req)
        if not 'method' in payload or not payload['method'] == 'ticket.get':
            req.send_response(501)  # Method Not Implemented
            req.end_headers()
            return
        params = payload['params']
        content = json.dumps(dict(map(lambda id: (id, self.get(req, id)), params)), indent=4)
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(content))
        req.end_headers()
        req.write(content)

    def format(self, param):
        if isinstance(param, datetime):
            return {"__jsonclass__": ["datetime", param.isoformat()]}
        return param

    # if TicketSystem(self.env).resource_exists(resource):
    def get(self, req, id):
        ticket = Ticket(self.env, id)
        req.perm(ticket.resource).require('TICKET_VIEW')  # FIXME: skip instead fail
        return {  # like XmlRpcPlugin
            'id': id,
            'error': None,
            'result': [
                id,
                self.format(ticket.values['time']),
                self.format(ticket.values['changetime']),
                dict([(key, self.format(ticket.values[key])) for key in ticket.values
                    if key in self.config.getlist('ticket', 'decorate_fields')])
            ]
        }

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if True:  # any template
            add_script(req, "contextchrome/js/ticketlinkdecorator.js")
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


class WikiLinkNewDecolator(Component):
    """ set \"new\" css-class to wiki link if the page is young. age can set in [wiki]-wiki_new_info_second in trac.ini"""
    implements(IRequestHandler, IRequestFilter, ITemplateProvider)

    wiki_new_info_day = IntOption('wiki', 'wiki_new_info_second', '432000',
        doc=u"""age in seconds to add new icon. (Provided by !ContextChrome.!WikiLinkNewDecolator) """)

    # IRequestHandler Methods
    def match_request(self, req):
        return req.path_info == '/contextchrome/wikilinknew.jsonrpc'

    def process_request(self, req):
        payload = json.load(req)
        if not 'method' in payload or not payload['method'] == 'wiki.getPageInfo':
            req.send_response(501)  # Method Not Implemented
            req.end_headers()
            return
        params = payload['params']
        content = json.dumps(dict(map(lambda id: (id, self.get(req, id)), params)), indent=4)
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(content))
        req.end_headers()
        req.write(content)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if True:  # any template
            add_script(req, "contextchrome/js/wikilinknewdecorator.js")
            add_script_data(req, {'config__wiki__wiki_new_info_second': 
                self.config.getint('wiki', 'wiki_new_info_second')})
        return template, data, content_type

    def get(self, req, id):
        wikipage = WikiPage(self.env, id)
        req.perm(wikipage.resource).require('WIKI_VIEW')  # FIXME: skip instead fail
        now = datetime.now(req.tz)
        limit = self.config.getint('wiki', 'wiki_new_info_second')
        delta = now - wikipage.time
        return {  # like XmlRpcPlugin
            'id': id,
            'error': None,
            'result': [
                id,
                wikipage.time.isoformat(),
                delta.total_seconds(),
                limit > delta.days * 86400 + delta.seconds,  # True if page is new
            ]
        }

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

class InternalStylesheet(Component):
    """ Use internal stylesheet. Off to use your own site.css for \".new\" css-class."""
    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        add_stylesheet(req, "contextchrome/css/contextchrome.css")
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


class InterTracTicketLinkDecorator(Component):
    """ set css-class to type on external ticket. """
    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        add_script(req, "contextchrome/js/xdr.js")
        add_script(req, "contextchrome/js/intertracticketlinkdecorator.js")
        add_script_data(req, {'config__ticket__decolate_fields': self.config.getlist('ticket', 'decorate_fields')})
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('contextchrome', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
