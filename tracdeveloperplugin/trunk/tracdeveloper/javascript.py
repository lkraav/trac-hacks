# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Ryan Ollos
# Copyright (C) 2012-2013 Olemis Lang
# Copyright (C) 2008-2009 Noah Kantrowitz
# Copyright (C) 2008 Christoper Lenz
# Copyright (C) 2007-2008 Alec Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.web.api import IRequestFilter


class JavascriptDeveloperModule(Component):
    """Developer functionality for JavaScript in Trac."""

    implements(IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.session.get('developer.js.enable_debug') == '1' and \
           req.path_info == '/chrome/common/js/jquery.js':
            req.args['prefix'] = 'developer'
            req.args['filename'] = 'js/jquery-1.2.6.js'
        return handler

    def post_process_request(self, req, template, content_type):
        return template, content_type
