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
from trac.web.main import RequestDispatcher


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
                for dispatcher in self.dispatchers.values():
                    agent = dispatcher.authenticate(req)
                    if agent != 'anonymous':
                        req.authname = agent
                        req.environ['shared_cookie_auth'] = agent
                        return agent

        return None

    # Internal methods

    @property
    def dispatchers(self):
        if self._dispatchers is None:
            self._dispatchers = {}
            parent_dir, project = os.path.split(self.env.path)
            projects = [i for i in os.listdir(parent_dir)
                          if i != project and
                             os.path.isdir(os.path.join(parent_dir, i))]

            for project in projects:
                project_path = os.path.join(parent_dir, project)
                try:
                    env = open_environment(project_path)
                except TracError:
                    pass
                else:
                    self._dispatchers[project] = RequestDispatcher(env)
        return self._dispatchers
