# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

import os.path
import shutil
import tempfile
import unittest

from trac.test import EnvironmentStub
from tracusermanager.api import UserManager, User


class SessionUserStoreTestCase(unittest.TestCase):
    """Dummy test suite"""

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.env = EnvironmentStub(enable=['trac.*', 'tracusermanager.*'])
        self.env.path = os.path.join(self.basedir, 'trac-tempenv')
        os.mkdir(self.env.path)

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_create_user(self):

        # create user
        UserManager(self.env).create_user(
            User(username='cbalan', name="Catalin Balan",
                 email='cbalan@optaros.com'))

        # test
        result = {}
        for name, value in self.env.db_query("""
                SELECT name, value FROM session_attribute
                WHERE sid='cbalan' AND name IN ('enabled', 'name', 'email')
                ORDER BY name
                """):
            result[name] = value

        self.assertEqual(result['name'], 'Catalin Balan')
        self.assertEqual(result['email'], 'cbalan@optaros.com')
        self.assertEqual(result['enabled'], '1')
        self.assertEqual(len(result), 3)

    def test_create_user_1(self):

        # define user
        user = User()
        user.username = 'cbalan'
        user['email'] = 'cbalan@optaros.com'
        user['name'] = 'Catalin Balan'

        # create user
        UserManager(self.env).create_user(user)

        # test
        result = dict((name, value) for name, value in self.env.db_query("""
            SELECT name, value FROM session_attribute
            WHERE sid='cbalan' AND name IN ('enabled', 'name', 'email')
            ORDER BY name
            """))

        self.assertEqual(result['name'], 'Catalin Balan')
        self.assertEqual(result['email'], 'cbalan@optaros.com')
        self.assertEqual(result['enabled'], '1')
        self.assertEqual(len(result), 3)

    def test_get_user(self):

        # create user
        UserManager(self.env).create_user(
            User(username='cbalan', name="Catalin Balan",
                 email='cbalan@optaros.com'))

        # get user
        user = UserManager(self.env).get_user('cbalan')

        # test
        self.assertEqual(user['name'], 'Catalin Balan')
        self.assertEqual(user['email'], 'cbalan@optaros.com')

    def test_save_user(self):

        # create user
        UserManager(self.env).create_user(
            User(username='cbalan', name="Catalin Balan",
                 email='cbalan@optaros.com'))

        # get user
        user = UserManager(self.env).get_user('cbalan')
        user['bio'] = "Some bio..."
        user.save()

        user_reloaded = UserManager(self.env).get_user('cbalan')
        # test
        self.assertEqual(user_reloaded['name'], 'Catalin Balan')
        self.assertEqual(user_reloaded['email'], 'cbalan@optaros.com')
        self.assertEqual(user_reloaded['bio'], 'Some bio...')

    def test_get_active_users(self):

        # create users
        UserManager(self.env).create_user(
            User(username='cbalan', name="Catalin Balan",
                 email='cbalan@optaros.com'))
        UserManager(self.env).create_user(
            User(username='aculapov', name="Andrei Culapov",
                 email='aculapov@optaros.com'))

        # get active users
        active_users = UserManager(self.env).get_active_users()

        # test
        self.assertEqual(active_users[0].username, 'cbalan')
        self.assertEqual(active_users[1].username, 'aculapov')
        self.assertEqual(len(active_users), 2)

    def test_search_users_1(self):
        # create users
        UserManager(self.env).create_user(
            User(username='cbalan', name="Catalin Balan",
                 email='cbalan@optaros.com', company='opt'))
        UserManager(self.env).create_user(
            User(username='aculapov', name="Andrei Culapov",
                 email='aculaposv@optaros.com', company='ros'))
        UserManager(self.env).create_user(
            User(username='acudlapov', name="Andrei Culapov",
                 email='aculapov@optaros.com', company='ros'))

        # search users using "default_attributes"
        search_result = UserManager(self.env).search_users(
            User(email='%culapov%'))

        # test
        self.assertEqual(len(search_result), 1)

    def test_search_users_2(self):
        # create users
        UserManager(self.env).create_user(
            User(username='cbalan', name="Catalin Balan",
                 email='cbalan@optaros.com', company='opt'))
        UserManager(self.env).create_user(
            User(username='aculapov', name="Andrei Culapov",
                 email='aculaposv@optaros.com', company='ros'))
        UserManager(self.env).create_user(
            User(username='acudlapov', name="Andrei Culapov",
                 email='aculapov@optaros.com', company='ros'))

        # search users using "changes"
        user_template = User()
        user_template['email'] = '%culapov%'
        search_result = UserManager(self.env).search_users(user_template)

        # test
        self.assertEqual(len(search_result), 1)

    def test_delete_attribute(self):
        # create users
        UserManager(self.env).create_user(
            User(username='cbalan', name="Catalin Balan",
                 email='cbalan@optaros.com', company='opt'))
        UserManager(self.env).create_user(
            User(username='aculapov', name="Andrei Culapov",
                 email='aculaposv@optaros.com', company='ros'))
        UserManager(self.env).create_user(
            User(username='acudlapov', name="Andrei Culapov",
                 email='aculapov@optaros.com', company='ros'))

        # test before
        result = dict((name, value) for name, value in self.env.db_query("""
                SELECT name, value FROM session_attribute
                WHERE sid='cbalan' ORDER BY name
                """))
        self.assertEqual(len(result), 4)

        # delete attribute
        user = UserManager(self.env).get_user('cbalan')
        del user['name']
        del user['email']
        user.save()

        # test after

        result = dict((name, value) for name, value in self.env.db_query("""
            SELECT name, value FROM session_attribute
            WHERE sid='cbalan' ORDER BY name
            """))
        self.assertEqual(len(result), 2)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SessionUserStoreTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
