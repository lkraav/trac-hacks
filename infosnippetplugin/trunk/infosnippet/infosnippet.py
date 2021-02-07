# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Clemens
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.config import *
from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import (
    ITemplateProvider, add_script, add_script_data, add_stylesheet)


class InfoSnippetComponent(Component):
    """
    This component uses Javascript to provide a text information box (snippet) with basic ticket infos like title and URL.
    """

    implements(IRequestFilter, ITemplateProvider)

    conf_section = ConfigSection('infosnippet',
      """
      This config section belongs to the Info-Snippet plugin.
      Its purpose is to gather basic information (like title and ULR) and copy it to the clipboard. 
      """)

    nav_option = ChoiceOption('infosnippet','nav',
      ['all','ticket','wiki','none'],
      """Specifies if the 'INFO' menu item shall appear in the context navigation menu at top of the page.
      Clicking this menu option will not navigate but instead copy the information snippet (as text) into the system clipboard.

      Valid options are: 
      - `ticket` only for ticket pages
      - `wiki` only for wiki pages
      - `all` for both of them
      - `none` neither of them
      """)

    box_option = ChoiceOption('infosnippet','box',
      ['all','ticket','wiki','none'],
      """Specifies if the 'Info Snippet' box shall appear near the bottom of the page.
      This is a box containing elemental information like title and URL for instance. 

      Valid options are: 
      - `ticket` only for ticket pages
      - `wiki` only for wiki pages
      - `all` for both of them
      - `none` neither of them
      """)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):

        if template in ('ticket.html'):

            ticket = data['ticket']
            if ticket is not None:
                self.log.debug("Preparing InfoSnippet plugin for ticket.")
                add_script_data(req, info={
                          'navoption':self.nav_option,
                          'boxoption':self.box_option,
                          'projectname':self.env.project_name,
                          'ticketid':str(ticket.id),
                          'ticketsummary':ticket['summary']})
                add_script(req, 'info/infosnippet.js')
                add_stylesheet(req, 'info/infosnippet.css')

        if template in ('wiki_view.html'):
            self.log.debug("Preparing InfoSnippet plugin for wiki.")
            page = data.get('page')
            if page is not None:
                self.log.debug(page.name)
           
                add_script_data(req, info={
                          'navoption':self.nav_option,
                          'boxoption':self.box_option,
                          'projectname':self.env.project_name,
                          'page':page.name})
                add_script(req, 'info/infosnippet.js')
                add_stylesheet(req, 'info/infosnippet.css')

        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('info', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
