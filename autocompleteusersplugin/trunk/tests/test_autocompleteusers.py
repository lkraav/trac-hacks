# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Jun Omae <jun66j5@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from cStringIO import StringIO

from trac.test import EnvironmentStub, MockPerm
from trac.util.datefmt import utc
from trac.web.api import Request, RequestDone

from autocompleteusers.autocompleteusers import AutocompleteUsers


class Test(object):

    def setup_method(self, method):
        self.env = EnvironmentStub(default_data=True)
        self.mod = AutocompleteUsers(self.env)

    def teardown_method(self, method):
        self.env.reset_db()

    if hasattr(EnvironmentStub, 'insert_users'):
        def _insert_user(self, username, name, email):
            self.env.insert_users([(username, name, email)])
    else:
        def _insert_user(self, username, name, email):
            self.env.known_users.append((username, name, email))

    def _insert_test_users(self):
        self._insert_user('alice', u'Alïcé', 'alice@example.org')
        self._insert_user('charlie', None, 'charlie@example.org')
        self._insert_user('bob', u'Böb', None)

    def _make_environ(self, scheme='http', server_name='example.org',
                      server_port=80, method='GET', script_name='/trac',
                      **kwargs):
        environ = {'wsgi.url_scheme': scheme, 'wsgi.input': StringIO(''),
                   'REQUEST_METHOD': method, 'SERVER_NAME': server_name,
                   'SERVER_PORT': server_port, 'SCRIPT_NAME': script_name}
        environ.update(kwargs)
        return environ

    def _make_req(self, args={}):
        buf = StringIO()
        environ = self._make_environ(PATH_INFO='/subjects')
        req = Request(environ, lambda status, headers: buf.write)
        req.authname = 'anonymous'
        req.args.update(args)
        req.arg_list = [(name, value)
                        for name in req.args
                        for value in req.args.getlist(name)]
        req.perm = MockPerm()
        req.session = {}
        req.chrome = {}
        req.tz = utc
        req.locale = None
        req.lc_time = 'iso8601'
        req.form_token = None
        req.response_sent = buf
        return req

    def _process_request(self, req):
        assert self.mod.match_request(req)
        try:
            self.mod.process_request(req)
            raise AssertionError('not raising RequestDone')
        except RequestDone:
            return req.response_sent.getvalue().decode('utf-8')

    def test_no_users(self):
        req = self._make_req(args={'users': '1'})
        assert '' == self._process_request(req)

    def test_users(self):
        self._insert_test_users()
        req = self._make_req(args={'users': '1'})
        assert self._process_request(req) == \
            u'alice|<alice@example.org> |Alïcé\n' \
            u'bob||Böb\n' \
            u'charlie|<charlie@example.org> |'
        req = self._make_req(args={'users': '1', 'q': 'cH'})
        assert self._process_request(req) == u'charlie|<charlie@example.org> |'

    def test_users_without_email_view(self):
        self._insert_test_users()
        req = self._make_req(args={'users': '1'})
        req.perm = {}  # no permissions
        assert self._process_request(req) == \
            u'alice|<alice@…> |Alïcé\n' \
            u'bob||Böb\n' \
            u'charlie|<charlie@…> |'
        req = self._make_req(args={'users': '1', 'q': 'B'})
        assert self._process_request(req) == u'bob||Böb'

    def test_users_with_groups(self):
        self._insert_test_users()
        req = self._make_req(args={'users': '1', 'groups': '1'})
        assert self._process_request(req) == \
            u'alice|<alice@example.org> |Alïcé\n' \
            u'bob||Böb\n' \
            u'charlie|<charlie@example.org> |\n' \
            u'anonymous||group\n' \
            u'authenticated||group'
        req = self._make_req(args={'users': '1', 'groups': '1', 'q': 'An'})
        assert self._process_request(req) == u'anonymous||group'
