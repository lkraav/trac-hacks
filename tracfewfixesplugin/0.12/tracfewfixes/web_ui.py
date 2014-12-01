# -*- coding: utf-8 -*-

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script


class FewFixesWebModule(Component):

    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('attachment.html', 'ticket.html'):
            add_script(req, 'tracfewfixes/disable-on-submit.js')
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        yield 'tracfewfixes', resource_filename(__name__, 'htdocs')

    def get_templates_dirs(self):
        return ()
