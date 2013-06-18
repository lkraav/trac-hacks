#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

# Tested on
#  - Internet Explorer 10.0.9200.16618
#  - Google Chrome 27.0.1453.110 m
#  - Firefox 18.0.1

from trac.core import Component, implements
from trac.web.api import RequestDone
from trac.config import Option

try:
    from tracrpc.api import IRPCProtocol, IXMLRPCHandler
    from tracrpc.json_rpc import JsonRpcProtocol

    class CrossOriginResourceSharingEnabler(Component):
        """Enable CORS access from another site for XmlRpcPlugin; see: http://www.w3.org/TR/cors/"""
        implements(IRPCProtocol, IXMLRPCHandler)

        jsonrpc_origin = Option('rpc', 'jsonrpc_origin', '',
        doc=u"""SP separated permitted origins;
        Where do you want to permit requests from;
        for jsonrpc Cross-Origin Resource Sharing.
        http://example.com/path for specified, blank for nowhere,
        {{{*}}}(asterisk) for anywhere to permit.
        See: http://www.w3.org/TR/cors/, rfc:6454.
        (Provided by !ContextChrome.!CrossOriginResourceSharingEnabler)""")

        wrapped = None

        # IRPCProtocol methods
        def rpc_info(self):
            return 'CORS', 'Cross Origin Resource Sharing Enabler'

        def rpc_match(self):
            if not self.wrapped:
                self.wrap()
            yield ('jsonrpc', 'text/plain')

        def parse_rpc_request(self, req, content_type):
            return {'method': 'CORS.dummy'}

        def send_rpc_result(self, req, result):
            jsonrpc_origin = self.config.get('rpc', 'jsonrpc_origin')
            req.send_response(200)
            req.send_header('Content-Length', 0)
            req.send_header('Access-Control-Allow-Origin', jsonrpc_origin)  # req.get_header('Origin'))
            req.send_header('Access-Control-Allow-Headers', 'Content-Type')
            req.end_headers()
            req.write('\n')
            raise RequestDone()

        def send_rpc_error(self, req, e):
            req.send_response(500)
            req.send_header('Content-Length', 0)
            req.end_headers()
            req.write('\n')
            raise RequestDone()

        #IXMLRPCHandler methods
        def xmlrpc_namespace(self):
            return 'CORS'

        def xmlrpc_methods(self):
            yield (None, None, lambda req: None, 'dummy')

        def wrap(self):
            jsonRpcProtocol = self.compmgr[JsonRpcProtocol]
            if not jsonRpcProtocol:
                self.wrapped = 1  # avoid to wrap again
                return

            def _send_response(*args, **kwargs):  # hook method
                jsonrpc_origin = self.config.get('rpc', 'jsonrpc_origin')
                args[0].send_header('Access-Control-Allow-Origin', jsonrpc_origin)  # args[0].get_header('Origin'))
                return self.wrapped(*args, **kwargs)
            self.wrapped = jsonRpcProtocol._send_response
            jsonRpcProtocol._send_response = _send_response

except:
    class CrossOriginResourceSharingEnabler(Component):
        """(Disabled; XmlRpcPlugin required. See http://trac-hacks.org/wiki/XmlRpcPlugin.)"""
        pass
