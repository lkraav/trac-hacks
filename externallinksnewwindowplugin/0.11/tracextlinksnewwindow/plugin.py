# -*- coding: utf-8 -*-
""" Copyright (c) 2008-2009 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $URL$

    This is Free Software under the GPL v3!
"""

from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script


class ExtLinksNewWindowPlugin(Component):
    """Opens external links in new window
    """
    implements(IRequestFilter, ITemplateProvider)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('extlinksnewwindow', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'extlinksnewwindow/extlinks.js')
        return template, data, content_type
