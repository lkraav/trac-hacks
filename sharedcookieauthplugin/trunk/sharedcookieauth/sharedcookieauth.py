# -*- coding: utf8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# Copyright (C) 2012 Lars Wireen <lw@agitronic.se>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os

from trac.core import Component, TracError, implements
from trac.env import open_environment
from trac.web.api import IAuthenticator
from trac.web.main import RequestDispatcher, get_environments


class SharedCookieAuth(Component):

    implements(IAuthenticator)

    # IAuthenticator methods

    def authenticate(self, req):
        if not self.is_delegated_auth(req) and \
                'trac_auth' in req.incookie:
            for dispatcher in self.get_dispatchers(req):
                authname = dispatcher.authenticate(req)
                if authname != 'anonymous':
                    self.revert_expire_cookie(req)
                    return authname

    # Internal methods

    def is_delegated_auth(self, req):
        """Return true if authentication has been delegated from
        another project.
        """
        req_env_name = os.path.split(req.base_path)[-1]
        env_name = os.path.split(self.env.path)[-1]
        return req_env_name and env_name != req_env_name

    def revert_expire_cookie(self, req):
        if 'trac_auth' in req.outcookie and \
                req.outcookie['trac_auth']['expires'] == -10000:
            del req.outcookie['trac_auth']

    def get_dispatchers(self, req):
        dispatchers = []
        for env_path in get_environments(req.environ).values():
            if env_path != self.env.path:
                try:
                    env = open_environment(env_path, use_cache=True)
                except TracError:
                    pass
                else:
                    dispatchers.append(RequestDispatcher(env))
        return dispatchers
