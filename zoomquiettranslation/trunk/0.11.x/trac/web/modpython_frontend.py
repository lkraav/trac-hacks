# -*- coding: utf-8 -*-
#
# Copyright (C) 2004-2007 Edgewall Software
# Copyright (C) 2004-2007 Christopher Lenz <cmlenz@gmx.de>
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Christopher Lenz <cmlenz@gmx.de>
#         Matthew Good <trac@matt-good.net>

import os
import pkg_resources
import urllib

from mod_python import apache
try:
    from mod_python import version
except ImportError:
    version = "< 3.2"

from trac import __version__ as VERSION
from trac.web.main import dispatch_request
from trac.web.wsgi import WSGIGateway, _ErrorsWrapper


class InputWrapper(object):

    def __init__(self, req):
        self.req = req

    def close(self):
        pass

    def read(self, size=-1):
        return self.req.read(size)

    def readline(self, size=-1):
        return self.req.readline(size)

    def readlines(self, hint=-1):
        return self.req.readlines(hint)


class ModPythonGateway(WSGIGateway):

    wsgi_multithread = apache.mpm_query(apache.AP_MPMQ_IS_THREADED) > 0
    wsgi_multiprocess = apache.mpm_query(apache.AP_MPMQ_IS_FORKED) > 0

    def __init__(self, req, options):
        environ = {}
        environ.update(apache.build_cgi_env(req))

        environ['trac.web.frontend'] = 'mod_python'
        environ['trac.web.version'] = version

        if 'TracEnv' in options:
            environ['trac.env_path'] = options['TracEnv']
        if 'TracEnvParentDir' in options:
            environ['trac.env_parent_dir'] = options['TracEnvParentDir']
        if 'TracEnvIndexTemplate' in options:
            environ['trac.env_index_template'] = options['TracEnvIndexTemplate']
        if 'TracTemplateVars' in options:
            environ['trac.template_vars'] = options['TracTemplateVars']
        if 'TracLocale' in options:
            environ['trac.locale'] = options['TracLocale']

        if 'TracUriRoot' in options:
            # Special handling of SCRIPT_NAME/PATH_INFO for mod_python, which
            # tends to get confused for whatever reason
            root_uri = options['TracUriRoot'].rstrip('/')
            request_uri = environ['REQUEST_URI'].split('?', 1)[0]
            if not request_uri.startswith(root_uri):
                raise ValueError('TracUriRoot set to %s but request URL '
                                 'is %s' % (root_uri, request_uri))
            environ['SCRIPT_NAME'] = root_uri
            environ['PATH_INFO'] = urllib.unquote(request_uri[len(root_uri):])

        egg_cache = req.subprocess_env.get('PYTHON_EGG_CACHE')
        if egg_cache:
            os.environ['PYTHON_EGG_CACHE'] = egg_cache

        WSGIGateway.__init__(self, environ, InputWrapper(req),
                             _ErrorsWrapper(lambda x: req.log_error(x)))
        self.req = req

    def _send_headers(self):
        assert self.headers_set, 'Response not started'

        if not self.headers_sent:
            status, headers = self.headers_sent = self.headers_set
            self.req.status = int(status[:3])
            for name, value in headers:
                if name.lower() == 'content-length':
                    self.req.set_content_length(int(value))
                elif name.lower() == 'content-type':
                    self.req.content_type = value
                else:
                    self.req.headers_out.add(name, value)

    def _sendfile(self, fileobj):
        self._send_headers()
        self.req.sendfile(fileobj.name)

    def _write(self, data):
        self._send_headers()
        try:
            self.req.write(data)
        except IOError, e:
            if 'client closed connection' not in str(e):
                raise


def handler(req):
    pkg_resources.require('Trac==%s' % VERSION)
    gateway = ModPythonGateway(req, req.get_options())
    gateway.run(dispatch_request)
    return apache.OK
