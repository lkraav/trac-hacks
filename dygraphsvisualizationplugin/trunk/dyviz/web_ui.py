# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Jon Ashley <trac@zelatrix.plus.com>
# All rights reserved.
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re

from trac.config import ListOption
from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.main import IRequestFilter, IRequestHandler

class VisualizationModule(Component):
    implements(IRequestHandler, ITemplateProvider, IRequestFilter)

    SECTION = 'dyviz'
    DEFAULTS = {
        'source': 'table',
        'query': '',
        'selector': 'table.listing.tickets',
        'options': 'width:600,height:400',
    }

    reports = ListOption(SECTION, 'reports', default=[],
            doc="List of report numbers to treat as queues(?)")

    # ITemplateProvider methods.
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('dyviz', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IRequestFilter methods.
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if self._is_valid_request(req):
            add_stylesheet(req, 'dyviz/dyviz.css')
            add_script(req, 'dyviz/dygraph-combined-dev.js')
            add_script(req, 'dyviz/dyviz.js')
            add_script(req, '/dyviz/dyviz.html')
        return template, data, content_type

    # IRequestHandler methods.
    def match_request(self, req):
        return req.path_info.startswith('/dyviz/')

    def process_request(self, req):
        data = self._get_data(req)
        return 'dyviz.html', data, 'text/javascript'

    # Private methods.
    def _is_valid_request(self, req):
        """ Checks permissions and that page is visualizable. """
        if req.perm.has_permission('TICKET_VIEW') and \
                'action=' not in req.query_string and \
                self._get_section(req):
            return True
        return False

    def _get_section(self, req, check_referer=False):
        """ Returns the trac.ini section that best matches the page url.
            There's a default section [dyviz] plus regex defined sections.
            The 'options' field is passed directly to dygraphs.

              [dyviz]
              reports = 11,12
              options = width:400,height:300

              [dyviz.report/12]
              options = colors:['red','orange']

              [dyviz.milestone]
              options = plotter:barChartPlotter

            In this example, here are results for different page urls:

              /report/1      ->  None
              /report/11     ->  'dyviz'
              /report/12     ->  'dyviz.report/12'
              /milestone/m1  ->  'dyviz.milestone'
        """
        if check_referer:
            path = req.environ.get('HTTP_REFERER','')
        else:
            path = req.path_info

        # check regex sections
        for section in self.env.config.sections():
            if not section.startswith('%s.' % self.SECTION):
                continue
            section_re = re.compile(section[len(self.SECTION)+1:])
            if section_re.search(path):
                return section

        # check reports list
        report_re = re.compile(r"/report/(?P<num>[1-9][0-9]*)")
        match = report_re.search(req.path_info)
        if match:
            report = match.groupdict()['num']
            if report in self.reports:
                return self.SECTION

        return None

    def _get_data(self, req):
        """Return the template data for the given request url."""
        data = {}
        section = self._get_section(req, check_referer=True)

        # override [dyviz] with regex section
        for key,default in self.DEFAULTS.items():
            data[key] = self.env.config.get(self.SECTION,key,default) # [dyviz]
            if section != self.SECTION:
                data[key] = self.env.config.get(section,key,data[key])

        # Redo options - make additive.
        key,default = 'options',self.DEFAULTS['options']
        data[key] = self.env.config.get(self.SECTION,key,default) # [dyviz]
        if section != self.SECTION:
            options = self.env.config.get(section,key,data[key])
            if data[key] != options:
                data[key] = (data[key] + ',' + options).strip(',')

        return data
