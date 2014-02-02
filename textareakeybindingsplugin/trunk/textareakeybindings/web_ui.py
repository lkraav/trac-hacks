# -*- coding: utf-8 -*-

import pkg_resources

from trac.core import *
from trac.web import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script


class TextareaKeyBindingsModule(Component):
    """Better keybindings for <textarea> controls."""

    implements(ITemplateProvider, IRequestFilter)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if (req.path_info.startswith('/wiki') or
            req.path_info.startswith('/ticket') or
            req.path_info.startswith('/newticket') or
            req.path_info.startswith('/discussion')):
            if req.method == 'GET':
                self.env.log.info('Injecting textareakeybindings.js')
                add_script(req, 'textareakeybindings/js/textareakeybindings.js')
        return (template, data, content_type)

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('textareakeybindings', pkg_resources.resource_filename('textareakeybindings', 'htdocs'))]

    def get_templates_dirs(self):
        return []
