# -*- coding: utf-8 -*-

import binascii

from trac.core import Component, implements
from trac.config import ListOption
from trac.web.api import IRequestFilter, RequestDone, IAuthenticator

from acct_mgr.api import AccountManager


__all__ = ['HTTPAuthFilter']


class HTTPAuthFilter(Component):
    """Request filter and handler to provide HTTP authentication."""

    paths = ListOption('httpauth', 'paths',
                       default='/login/xmlrpc,/login/jsonrpc',
                       doc='Paths to force HTTP authentication on.')

    formats = ListOption('httpauth', 'formats',
                         doc='Request formats to force HTTP authentication on')

    implements(IRequestFilter, IAuthenticator)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        check = req.path_info.startswith(tuple(self.paths)) or \
                req.args.get('format') in self.formats
        if check and not self._check_password(req):
            self.log.info(
                'HTTPAuthFilter: No/bad authentication data given, returing 403')
            return self
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # IRequestHandler methods (sort of)

    def process_request(self, req):
        if req.session:
            req.session.save()  # Just in case

        auth_req_msg = b'Authentication required'
        req.send_response(401)
        req.send_header('WWW-Authenticate', 'Basic realm="Control Panel"')
        req.send_header('Content-Type', 'text/plain')
        req.send_header('Pragma', 'no-cache')
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Length', str(len(auth_req_msg)))
        if req.get_header('Content-Length'):
            req.send_header('Connection', 'close')
        req.end_headers()

        if req.method != 'HEAD':
            req.write(auth_req_msg)
        raise RequestDone

    # IAuthenticator methods

    def authenticate(self, req):
        user = self._check_password(req)
        if user:
            req.environ['REMOTE_USER'] = user
            self.log.debug('HTTPAuthFilter: Authentication okay for %s', user)
            return user

    # Internal methods

    def _check_password(self, req):
        header = req.get_header('Authorization')
        if not header:
            return None
        values = header.split()
        if values[0].lower() != 'basic':
            return None
        if len(values) != 2:
            return None
        try:
            creds = binascii.a2b_base64(values[1])
        except binascii.Error:
            return None
        creds = creds.decode('latin1')
        if ':' not in creds:
            return None
        user, passwd = creds.split(':')
        if AccountManager(self.env).check_password(user, passwd):
            return user
