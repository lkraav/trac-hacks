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

    def __init__(self):
        self._dispatchers = None

    # IAuthenticator methods

    def authenticate(self, req):
        if req.remote_user:
            return req.remote_user

        if 'shared_cookie_auth' in req.environ:
            return req.environ['shared_cookie_auth']
        else:
            req.environ['shared_cookie_auth'] = None
            if 'trac_auth' in req.incookie:
                if self._dispatchers is None:
                    self._dispatchers = self.get_dispatchers(req)
                for dispatcher in self._dispatchers:
                    agent = dispatcher.authenticate(req)
                    if agent != 'anonymous':
                        req.authname = agent
                        req.environ['shared_cookie_auth'] = agent
                        self.revert_expire_cookie(req)
                        return agent

        return None

    # Internal methods

    def revert_expire_cookie(self, req):
        if 'trac_auth' in req.outcookie and \
                req.outcookie['trac_auth']['expires'] == -10000:
            del req.outcookie['trac_auth']

    def get_dispatchers(self, req):
        dispatchers = []
        for env_path in get_environments(req.environ).values():
            try:
                env = open_environment(env_path)
            except TracError:
                pass
            else:
                dispatchers.append(RequestDispatcher(env))
        return dispatchers
