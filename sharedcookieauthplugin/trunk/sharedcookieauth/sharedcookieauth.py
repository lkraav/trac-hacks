"""
SharedCookieAuth:
a plugin for Trac to share cookies between Tracs
http://trac.edgewall.org
"""

import os

from trac.core import *
from trac.web.api import IAuthenticator
from trac.web.main import RequestDispatcher
from trac.env import open_environment


class SharedCookieAuth(Component):

    ### class-level data
    implements(IAuthenticator)

    ### method for IAuthenticator

    def authenticate(self, req):

        if req.remote_user:
            return req.remote_user

        if 'shared_cookie_auth' in req.environ:
            return req.environ['shared_cookie_auth']
        else:
            req.environ['shared_cookie_auth'] = None
            if req.incookie.has_key('trac_auth'):
                for project, dispatcher in self.dispatchers().items():
                    agent = dispatcher.authenticate(req)
                    if agent != 'anonymous':
                        req.authname = agent
                        req.environ['shared_cookie_auth'] = agent
                        return agent

        return None

    ### internal methods

    def dispatchers(self):
        if not hasattr(self, '_dispatchers'):

            dispatchers = {}
            base_path, project = os.path.split(self.env.path)
            projects = [ i for i in os.listdir(base_path)
                         if i != project ]

            for project in projects:
                path = os.path.join(base_path, project)
                try:
                    env = open_environment(path)
                    rd = RequestDispatcher(env)
                except:
                    continue
                dispatchers[project] = rd

            self._dispatchers = dispatchers
        return self._dispatchers
