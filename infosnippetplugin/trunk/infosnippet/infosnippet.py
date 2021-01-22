# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Clemens
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, add_script, add_script_data, add_stylesheet)


class InfoSnippetComponent(Component):
    """
    This component uses Javascript to provide a text information box (snippet) with basic ticket infos like title and URL.
    """

    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('ticket.html'):
	    # self.log.debug("Clemens: Info Snippet running.")

            ticket = data['ticket']
            # TODO must check if this is was sucessful!!

            add_script_data(req, info={
                          'projectname':self.env.project_name,
                          'ticketid':str(ticket.id),
                          'ticketsummary':ticket['summary']})
            add_script(req, 'info/infosnippet.js')
            add_stylesheet(req, 'info/infosnippet.css')
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('info', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
