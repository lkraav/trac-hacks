# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Odd Simon Simonsen <oddsimons@gmail.com>
# Copyright (C) 2012-2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import doctest
import shutil
import tempfile
import unittest

from trac.core import implements
from trac.db.api import DatabaseManager
from trac.perm import IPermissionRequestor, PermissionCache, PermissionError
from trac.perm import PermissionSystem
from trac.resource import Resource
from trac.test import EnvironmentStub, Mock, MockPerm

import tractags.api

from tractags.db import TagSetup
from tractags.ticket import TicketTagProvider
from tractags.wiki import WikiTagProvider


class _BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=['trac.*', 'tractags.*'])
        self.env.path = tempfile.mkdtemp()
        self.perms = PermissionSystem(self.env)
        self.req = Mock(authname='editor')

        self.actions = ['TAGS_ADMIN', 'TAGS_MODIFY', 'TAGS_VIEW']
        self.db = self.env.get_db_cnx()
        setup = TagSetup(self.env)
        # Current tractags schema is setup with enabled component anyway.
        #   Revert these changes for getting default permissions inserted.
        self._revert_tractags_schema_init()
        setup.upgrade_environment(self.db)
        self.tag_s = tractags.api.TagSystem(self.env)

    def tearDown(self):
        self.db.close()
        # Really close db connections.
        self.env.shutdown()
        shutil.rmtree(self.env.path)

    # Helpers

    def _revert_tractags_schema_init(self):
        cursor = self.db.cursor()
        cursor.execute("DROP TABLE IF EXISTS tags")
        cursor.execute("DROP TABLE IF EXISTS tags_change")
        cursor.execute("DELETE FROM system WHERE name='tags_version'")
        cursor.execute("DELETE FROM permission WHERE action %s"
                       % self.db.like(), ('TAGS_%',))


class TagPolicyTestCase(_BaseTestCase):

    def setUp(self):
        _BaseTestCase.setUp(self)
        cursor = self.db.cursor()
        # Populate table with initial test data.
        cursor.executemany("""
            INSERT INTO tags
                   (tagspace, name, tag)
            VALUES (%s,%s,%s)
        """, [('wiki', 'PublicPage', 'anonymous:modify'),
              ('wiki', 'RestrictedPage', 'anonymous:-view'),
              ('wiki', 'RestrictedPage', 'classified'),
              ('wiki', 'UserPage', 'private'),
              ('wiki', 'UserPage', 'user:admin'),
             ])
        self.check = tractags.api.TagPolicy(self.env).check_permission
        self.env.config.set('trac', 'permission_policies',
                            'TagPolicy, DefaultPermissionPolicy')

    # Tests

    def test_action_granted(self):
        resource = Resource('wiki', 'PublicPage')
        self.assertEquals(self.check('WIKI_MODIFY', 'anonymous', resource,
                                     PermissionCache(self.env)), True)

    def test_action_revoked(self):
        resource = Resource('wiki', 'RestrictedPage')
        self.assertEquals(self.check('WIKI_VIEW', 'anonymous', resource,
                                     PermissionCache(self.env)), False)

    def test_meta_action_granted(self):
        resource = Resource('wiki', 'UserPage')
        self.assertEquals(self.check('WIKI_DELETE', 'user', resource,
                                     PermissionCache(self.env,
                                                     username='user')), True)
        self.assertEquals(self.check('WIKI_DELETE', 'other', resource,
                                     PermissionCache(self.env,
                                                     username='other')), None)


class TagSystemTestCase(_BaseTestCase):

    # Tests

    def test_available_actions(self):
        for action in self.actions:
            self.failIf(action not in self.perms.get_actions())

    def test_available_providers(self):
        # Standard implementations of DefaultTagProvider should be registered.
        seen = []
        for provider in [TicketTagProvider(self.env),
                         WikiTagProvider(self.env)]:
            self.failIf(provider not in self.tag_s.tag_providers)
            # Ensure unique provider references, a possible bug in Trac-0.11.
            self.failIf(provider in seen)
            seen.append(provider)

    def test_set_tags_no_perms(self):
        resource = Resource('wiki', 'WikiStart')
        tags = ['tag1']
        # Mock an anonymous request.
        self.req.perm = PermissionCache(self.env)
        self.assertRaises(PermissionError, self.tag_s.set_tags, self.req,
                          resource, tags)

    def test_set_tags(self):
        resource = Resource('wiki', 'WikiStart')
        tags = ['tag1']
        self.req.perm = PermissionCache(self.env, username='editor')
        # Shouldn't raise an error with appropriate permission.
        self.tag_s.set_tags(self.req, resource, tags)

    def test_query_no_args(self):
        # Regression test for query without argument,
        #   reported as th:ticket:7857.

        # Mock an anonymous request.
        self.req.perm = PermissionCache(self.env)
        self.assertEquals([(res, tags) for res, tags in
                           self.tag_s.query(self.req, query='')],
                          [])

    def test_get_taggable_realms(self):

        class HiddenTagProvider(tractags.api.DefaultTagProvider):

            implements(IPermissionRequestor)

            realm = 'hidden'

            # IPermissionRequestor method
            def get_permission_actions(self):
                return ['TEST_VIEW']

            # ITagProvider method overwrite
            def check_permission(self, perm, action):
                """Somewhat inaccessible tag provider."""
                return perm.has_permission('TEST_VIEW')

        all_realms = set(['hidden', 'ticket', 'wiki'])
        # Mock an anonymous request.
        perm = PermissionCache(self.env)
        self.assertEquals(all_realms - set(['hidden']),
                          self.tag_s.get_taggable_realms(perm))

        self.perms.grant_permission('testuser', 'TEST_VIEW')
        perm = PermissionCache(self.env, 'testuser')
        self.assertEquals(all_realms, self.tag_s.get_taggable_realms(perm))
        # Get realms unconditionally.
        self.assertEquals(all_realms, self.tag_s.get_taggable_realms())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(module=tractags.api))
    suite.addTest(unittest.makeSuite(TagPolicyTestCase, 'test'))
    suite.addTest(unittest.makeSuite(TagSystemTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
