# -*- coding: utf-8 -*-

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.ticket.query import QueryModule
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script


class FewFixesWebModule(Component):

    implements(IRequestFilter, ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if isinstance(handler, QueryModule):
            for name in ('order', 'max', 'report', 'group'):
                value = req.args.get(name)
                if isinstance(value, (list, tuple)):
                    if len(value) > 0:
                        req.args[name] = value[0]
                    else:
                        del req.args[name]
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
