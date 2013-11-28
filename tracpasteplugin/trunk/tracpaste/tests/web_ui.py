# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import tempfile
import unittest
import shutil
import tempfile
from trac.perm import PermissionSystem, PermissionCache, PermissionError
from trac.test import EnvironmentStub, Mock
from trac.web.href import Href
from trac.wiki.tests import formatter

from tracpaste.db import TracpasteSetup
from tracpaste.model import Paste
from tracpaste.web_ui import TracpastePlugin


class TracpastePluginTestCase(unittest.TestCase):

    def MockRequest(self, path_info, method, authname, **args):
        req = Mock(_redirect_url=None,
                   _status_code=None,
                   _response_headers={},
                   _response_body="",
                   chrome={},
                   end_headers=lambda: None,
                   href=self.href,
                   
                   args=dict(args),
                   
                   path_info=path_info,
                   method=method,
                   authname=authname,
                   perm=getattr(self, authname),
                   )
        def redirect(url):
            req._redirect_url = url
        req.redirect = redirect
        def send_response(code):
            req._status_code = code
        req.send_response = send_response
        def send_header(header, value):
            req._response_headers[header] = value
        req.send_header = send_header
        def write(body):
            req._response_body += body
        req.write = write

        return req

    def setUp(self):
        self.env = EnvironmentStub(
                enable=['trac.*', 'tracpaste.*'])
        self.env.path = tempfile.mkdtemp()
        self.db = self.env.get_db_cnx()

        setup = TracpasteSetup(self.env)
        setup.upgrade_environment(self.db)

        self.href = Href('/trac')

        self.admin = PermissionCache(self.env, 'admin')

        perms = PermissionSystem(self.env)
        perms.grant_permission('admin', 'PASTEBIN_ADMIN')
        self.backend = TracpastePlugin(self.env)

    def tearDown(self):
        self.db.close()
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    def test_basics(self):
        req = Mock(path_info='/pastebin',
                   authname='admin',
                   perm=self.admin,
                   href=self.href,
                   chrome={},
                   args={})
        self.assertEquals(True, self.backend.match_request(req))
        self.assertEquals(True, req.args['new_paste'])

    def test_download_content_length(self):

        req = self.MockRequest('/pastebin', "POST", 'admin',
                               data="This is my first paste!",
                               title="My first paste title")

        self.assertEquals(True, self.backend.match_request(req))
        resp = self.backend.process_request(req)
        self.assertIsNotNone(req._redirect_url)
        self.assertRegexpMatches(req._redirect_url, '/pastebin/\d+$')

        paste_id = int(req._redirect_url.split("/")[-1])

        req = self.MockRequest('/pastebin/%s' % paste_id, "GET", 'admin',
                               format="raw")
        self.assertEquals(True, self.backend.match_request(req))

        resp = self.backend.process_request(req)
        self.assertEquals(200, req._status_code)
        self.assertEquals('This is my first paste!', req._response_body)
        self.assertEquals('text/plain; charset=UTF-8', 
                          req._response_headers.get("Content-Type"))
        self.assertEquals(23, req._response_headers.get("Content-Length"))

    def test_download_unicode_content_length(self):
        req = self.MockRequest('/pastebin', "POST", 'admin',
                               data=u"漢字仮名交じり文",
                               title="My unicode paste title")

        self.assertEquals(True, self.backend.match_request(req))
        resp = self.backend.process_request(req)
        self.assertIsNotNone(req._redirect_url)
        self.assertRegexpMatches(req._redirect_url, '/pastebin/\d+$')

        paste_id = int(req._redirect_url.split("/")[-1])

        req = self.MockRequest('/pastebin/%s' % paste_id, "GET", 'admin',
                               format="raw")
        self.assertEquals(True, self.backend.match_request(req))

        resp = self.backend.process_request(req)
        self.assertEquals(200, req._status_code)
        self.assertEquals(u"漢字仮名交じり文".encode("utf-8"), req._response_body)
        self.assertEquals('text/plain; charset=UTF-8',
                          req._response_headers.get("Content-Type"))
        self.assertEquals(len(req._response_body),
                          req._response_headers.get("Content-Length"))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TracpastePluginTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
