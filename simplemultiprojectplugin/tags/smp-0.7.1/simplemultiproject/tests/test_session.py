# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#

import unittest
from trac.test import EnvironmentStub, MockRequest
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.session import \
    get_list_from_req_or_session, get_project_filter_settings
from simplemultiproject.tests.util import revert_schema


class TestGetListFromReqOrSession(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.req = MockRequest(self.env, username='Tester')
        self.session_key = "ctx.filter.tst"

    def tearDown(self):
        self.env.reset_db()

    def test_get_list_from_req_or_session(self):
        req = self.req
        session_key = self.session_key

        # Request object without args. Test for default values when session attribute is empty.
        self.assertIsNone(get_list_from_req_or_session(req, 'ctx', 'tst'))
        self.assertNotIn(session_key, req.session)
        self.assertEqual('foo', get_list_from_req_or_session(req, 'ctx', 'tst', 'foo'))
        self.assertEqual(0, len(req.session))
        self.assertIsInstance(get_list_from_req_or_session(req, 'ctx', 'tst', ['foo', 'bar']), list)

        # Request object without args. Test with given session data.
        req.session.update({u'ctx.filter.tst': u'bar'})
        self.assertEqual('bar', get_list_from_req_or_session(req, 'ctx', 'tst'))  # Ignore default value
        self.assertEqual('bar', get_list_from_req_or_session(req, 'ctx', 'tst', 'foo'))  # Ignore default value
        self.assertEqual('bar', get_list_from_req_or_session(req, 'ctx', 'tst', ['foo', 'bar']))  # Ignore default list value
        self.assertNotIsInstance(get_list_from_req_or_session(req, 'ctx', 'tst', ['foo', 'bar']), list)
        self.assertEqual(u'bar', req.session[u'ctx.filter.tst'])

        # Request object without args. Test with given session data being a list representation.
        req.session.update({u'ctx.filter.tst': u'bar,///,foo'})
        res = get_list_from_req_or_session(req, 'ctx', 'tst', ['foo_', 'bar_', 'baz_'])
        self.assertIsInstance(res, list)
        self.assertEqual(2, len(res), list)
        self.assertEqual(u'bar', res[0])
        self.assertEqual(u'foo', res[1])
        self.assertEqual(u'bar,///,foo', req.session[u'ctx.filter.tst'])


class TestGetListFromReqOrSessionArgs(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.req = MockRequest(self.env, username='Tester')
        self.session_key = "ctx.filter.tst"

    def tearDown(self):
        self.env.reset_db()

    def test_get_list_from_req_or_session_args(self):
        req = self.req
        session_key = self.session_key
        # Request object with arg (not a list) and no session attribute
        self.assertEqual(0, len(req.session))
        req.args['tst'] = 'bar_value'
        req.args['smp_update'] = '1'
        self.assertEqual('bar_value', get_list_from_req_or_session(req, 'ctx', 'tst'))  # Ignore default value
        self.assertEqual('bar_value', req.session['ctx.filter.tst'], "Session data not updated.")

        # Request object with arg (not a list) and populated session attribute
        req.session.update({u'ctx.filter.tst': u'bar'})
        req.args['smp_update'] = '1'
        req.args['tst'] = 'bar_value'
        # The value is taken from the request
        self.assertEqual('bar_value', get_list_from_req_or_session(req, 'ctx', 'tst'))  # Ignore default value
        # The session data was updated with the request value
        self.assertEqual('bar_value', req.session['ctx.filter.tst'], "Session data not updated, but it should.")

        # Request object with arg (list) and no session attribute
        del req.session[session_key]
        self.assertEqual(0, len(req.session))
        del req.args['smp_update']  # The session data will not be updated now
        req.args['tst'] = ['bar_value', 'foo_value']
        self.assertIsInstance(get_list_from_req_or_session(req, 'ctx', 'tst', ['foo', 'bar']), list)
        self.assertEqual(0, len(req.session), "Session data updated.")

        # Request object with arg (list) and no session attribute
        try:
            del req.session[session_key]
        except KeyError:
            pass
        self.assertEqual(0, len(req.session))
        req.args['smp_update'] = '1'
        req.args['tst'] = ['bar_value', 'foo_value']
        self.assertIsInstance(get_list_from_req_or_session(req, 'ctx', 'tst', ['foo', 'bar']), list)
        self.assertEqual(u'bar_value,///,foo_value', req.session['ctx.filter.tst'], "Session data not updated.")

        # Request object with arg (list) and populated session attribute
        req.session.update({u'ctx.filter.tst': u'bar'})
        req.args['tst'] = ['bar_value', 'foo_value']
        req.args['smp_update'] = '1'
        self.assertIsInstance(get_list_from_req_or_session(req, 'ctx', 'tst', ['foo', 'bar']), list)
        self.assertEqual(u'bar_value,///,foo_value', req.session['ctx.filter.tst'], "Session data not updated.")


class TestGet_project_filter_settings(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.req = MockRequest(self.env, username='Tester')
        self.session_key = "ctx.filter.tst"

    def tearDown(self):
        self.env.reset_db()

    def test_get_project_filter_settings(self):
        req = self.req
        session_key = self.session_key

        # Request object without args. Test for default values when session attribute is empty.
        self.assertIsNone(get_project_filter_settings(req, 'ctx', 'tst'))
        self.assertEqual(0, len(req.session))

        res = get_project_filter_settings(req, 'ctx', 'tst', 'foo')
        self.assertIsInstance(res, list)
        self.assertEqual(1, len(res))

        self.assertEqual(0, len(req.session))
        res = get_project_filter_settings(req, 'ctx', 'tst', ['foo', 'bar'])
        self.assertIsInstance(res, list)
        self.assertEqual('foo', res[0])
        self.assertEqual('bar', res[1])

        # Testing with proper request args.
        req.args['tst'] = ['foo', 'bar']
        res = get_project_filter_settings(req, 'ctx', 'tst')
        self.assertIsInstance(res, list)
        self.assertEqual('foo', res[0])
        self.assertEqual('bar', res[1])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGetListFromReqOrSession))
    suite.addTest(unittest.makeSuite(TestGetListFromReqOrSessionArgs))
    suite.addTest(unittest.makeSuite(TestGet_project_filter_settings))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
