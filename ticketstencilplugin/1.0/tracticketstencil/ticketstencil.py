# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket.model import Type
from trac.web.chrome import add_script, add_script_data, ITemplateProvider
from trac.web.main import IRequestFilter
from trac.wiki.api import WikiSystem
from trac.wiki.model import WikiPage


class TicketStencil(Component):
    implements(IRequestFilter, ITemplateProvider)

    def __init__(self):
        self.wiki_system = WikiSystem(self.env)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketstencil', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if not req.path_info.startswith('/newticket'):
            return template, data, content_type
        add_script(req, 'ticketstencil/ticketstencil.js')
        stencils = {}
        prefix_len = len('TicketStencil')
        all_types = [enum.name for enum in Type.select(self.env)]
        for name in self.wiki_system.get_pages('TicketStencil'):
            page = WikiPage(env = self.env, name = name)
            ticket_type = name[prefix_len:].lower()
            stencils[ticket_type] = page.text
            try:
                all_types.remove(ticket_type)
            except ValueError:
                pass
        # Set defaults for remaining ticket types
        for ticket_type in all_types:
            stencils[ticket_type.lower()] = ''

        # An internal dummy value. See JavaScript code.
        stencils['_ticketstencil_default_type'] = ''

        add_script_data(req, {'_tracticketstencil': stencils})
        return template, data, content_type
