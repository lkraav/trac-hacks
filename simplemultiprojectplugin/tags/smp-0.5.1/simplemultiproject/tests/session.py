# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#

from unittest import TestCase
from trac.web.api import Request
from trac.web.session import DetachedSession
from trac.test import EnvironmentStub, Mock
from simplemultiproject.session import get_list_from_req_or_session, get_project_filter_settings

__author__ = 'Cinc'


class TestGet_list_from_req_or_session(TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=["trac.*", "simplemultiproject.*"])
        self.env.upgrade()
        self.req = Mock(session=DetachedSession(self.env, 'Tester'), args={})
        self.session_key = "ctx.filter.tst"

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

        # Request object with arg (not a list) and no session attribute
        del req.session[session_key]
        self.assertEqual(0, len(req.session))
        req.args['tst'] = 'bar_value'
        req.args['smp_update'] = '1'
        self.assertEqual('bar_value', get_list_from_req_or_session(req, 'ctx', 'tst'))  # Ignore default value
        self.assertEqual('bar_value', req.session['ctx.filter.tst'], "Session data not updated.")

        # Request object with arg (not a list) and populated session attribute
        req.session.update({u'ctx.filter.tst': u'bar'})
        req.args['smp_update'] = '1'
        req.args['tst'] = 'bar_value'
        self.assertEqual('bar_value', get_list_from_req_or_session(req, 'ctx', 'tst'))  # Ignore default value
        self.assertEqual('bar_value', req.session['ctx.filter.tst'], "Session data not updated.")

        # Request object with arg (list) and no session attribute
        del req.session[session_key]
        self.assertEqual(0, len(req.session))
        del req.args['smp_update']
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


class TestGet_project_filter_settings(TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True, enable=["trac.*", "simplemultiproject.*"])
        self.env.upgrade()
        self.req = Mock(session=DetachedSession(self.env, 'Tester'), args={})
        self.session_key = "ctx.filter.tst"

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