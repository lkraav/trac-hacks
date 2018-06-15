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

import inspect
import re
import sys

from trac.core import *
from trac.mimeview import Mimeview
from trac.web.api import HTTPNotFound, IRequestHandler
from trac.web.chrome import web_context

from tracdeveloper.util import linebreaks

__all__ = ['APIDocumentation']


class APIDocumentation(Component):
    implements(IRequestHandler)

    mimetype_map = {
        'tracwiki': 'text/x-trac-wiki',
        'restructuredtext': 'text/x-rst',
    }

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/developer/doc(?:/(.*))?$', req.path_info)
        if match:
            req.args['name'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.require('TRAC_DEVELOP')
        modname, attrname = str(req.args['name']).split(':')
        try:
            module = sys.modules[modname]
            obj = getattr(module, attrname)
        except (KeyError, AttributeError), e:
            raise HTTPNotFound(e)

        formatter = self._get_formatter(module)

        data = {
            'module': modname,
            'name': attrname or modname,
            'doc': formatter(req, inspect.getdoc(obj)),
            'methods': self._get_methods(req, formatter, obj)
        }
        return 'developer/apidoc.html', data, None

    # Internal methods
    def _get_formatter(self, module):
        format = getattr(module, '__docformat__', 'default').split()[0]
        mimetype = self.mimetype_map.get(format)
        if not mimetype:
            return self._format_default

        def mimeview_formatter(req, text):
            mimeview = Mimeview(self.env)
            context = web_context(req)
            return mimeview.render(context, mimetype, text)
        return formatter

    def _format_default(self, req, text):
        return linebreaks(text)

    def _get_methods(self, req, formatter, cls, exclude_methods=None):
        methods = [getattr(cls, m) for m in dir(cls) if not m.startswith('_')
                   and m not in (exclude_methods or [])]
        return [{'name': m.__name__,
                 'args': inspect.formatargspec(*inspect.getargspec(m)),
                 'doc': formatter(req, inspect.getdoc(m))}
                for m in methods if inspect.ismethod(m)]
