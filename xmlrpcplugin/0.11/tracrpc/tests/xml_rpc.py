# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import os
import sys
import unittest

import xmlrpclib

from tracrpc.tests import rpc_testenv, TracRpcTestCase

class RpcXmlTestCase(TracRpcTestCase):

    def setUp(self):
        TracRpcTestCase.setUp(self)
        self.anon = xmlrpclib.ServerProxy(rpc_testenv.url_anon)
        self.user = xmlrpclib.ServerProxy(rpc_testenv.url_user)
        self.admin = xmlrpclib.ServerProxy(rpc_testenv.url_admin)

    def tearDown(self):
        TracRpcTestCase.tearDown(self)

    def test_xmlrpc_permission(self):
        # Test returned response if not XML_RPC permission
        rpc_testenv._tracadmin('permission', 'remove', 'anonymous',
                                'XML_RPC', wait=True)
        e = self.assertRaises(xmlrpclib.Fault,
                    self.anon.system.listMethods)
        self.assertEquals(403, e.faultCode)
        self.assertTrue('XML_RPC' in e.faultString)
        rpc_testenv._tracadmin('permission', 'add', 'anonymous',
                                        'XML_RPC', wait=True)

    def test_method_not_found(self):
        def local_test():
            self.admin.system.doesNotExist()
            self.fail("What? Method exists???")
        e = self.assertRaises(xmlrpclib.Fault, local_test)
        self.assertEquals(-32601, e.faultCode)
        self.assertTrue("not found" in e.faultString)

    def test_wrong_argspec(self):
        def local_test():
            self.admin.system.listMethods("hello")
            self.fail("Oops. Wrong argspec accepted???")
        e = self.assertRaises(xmlrpclib.Fault, local_test)
        self.assertEquals(1, e.faultCode)
        self.assertTrue("listMethods() takes exactly 2 arguments" \
                                    in e.faultString)

    def test_content_encoding(self):
        test_string = "øæåØÆÅàéüoö"
        # No encoding / encoding error
        def local_test():
            t_id = self.admin.ticket.create(test_string, test_string[::-1], {})
            self.admin.ticket.delete(t_id)
            self.fail("Expected ticket create to fail...")
        e = self.assertRaises(xmlrpclib.Fault, local_test)
        self.assertTrue(isinstance(e, xmlrpclib.Fault))
        self.assertEquals(-32700, e.faultCode)
        # Unicode version (encodable)
        from trac.util.text import to_unicode
        test_string = to_unicode(test_string)
        t_id = self.admin.ticket.create(test_string, test_string[::-1], {})
        self.assertTrue(t_id > 0)
        result = self.admin.ticket.get(t_id)
        self.assertEquals(result[0], t_id)
        self.assertEquals(result[3]['summary'], test_string)
        self.assertEquals(result[3]['description'], test_string[::-1])
        self.assertEquals(unicode, type(result[3]['summary']))
        self.admin.ticket.delete(t_id)

    def test_to_and_from_datetime(self):
        from datetime import datetime
        from trac.util.datefmt import to_datetime, utc
        from tracrpc.xml_rpc import to_xmlrpc_datetime, from_xmlrpc_datetime
        now = to_datetime(None, utc)
        now_timetuple = now.timetuple()[:6]
        xmlrpc_now = to_xmlrpc_datetime(now)
        self.assertTrue(isinstance(xmlrpc_now, xmlrpclib.DateTime),
                "Expected xmlprc_now to be an xmlrpclib.DateTime")
        self.assertEquals(str(xmlrpc_now), now.strftime("%Y%m%dT%H:%M:%S"))
        now_from_xmlrpc = from_xmlrpc_datetime(xmlrpc_now)
        self.assertTrue(isinstance(now_from_xmlrpc, datetime),
                "Expected now_from_xmlrpc to be a datetime")
        self.assertEquals(now_from_xmlrpc.timetuple()[:6], now_timetuple)
        self.assertEquals(now_from_xmlrpc.tzinfo, utc)

    def test_resource_not_found(self):
        # A Ticket resource
        e = self.assertRaises(xmlrpclib.Fault, self.admin.ticket.get, 2147483647)
        self.assertEquals(e.faultCode, 404)
        self.assertEquals(e.faultString,
                'Ticket 2147483647 does not exist.')
        # A Wiki resource
        e = self.assertRaises(xmlrpclib.Fault, self.admin.wiki.getPage,
                            "Test", 10)
        self.assertEquals(e.faultCode, 404)
        self.assertEquals(e.faultString,
                'Wiki page "Test" does not exist at version 10')

    def test_xml_encoding_special_characters(self):
        tid1 = self.admin.ticket.create(
                            'One & Two < Four', 'Desc & ription\nLine 2', {})
        ticket = self.admin.ticket.get(tid1)
        try:
            self.assertEquals('One & Two < Four', ticket[3]['summary'])
            self.assertEquals('Desc & ription\r\nLine 2',
                            ticket[3]['description'])
        finally:
            self.admin.ticket.delete(tid1)

    def test_xml_encoding_invalid_characters(self):
        # Enable ticket manipulator
        plugin = os.path.join(rpc_testenv.tracdir, 'plugins',
                              'InvalidXmlCharHandler.py')
        open(plugin, 'w').write(
        "from trac.core import *\n"
        "from tracrpc.api import IXMLRPCHandler\n"
        "class UniChr(Component):\n"
        "    implements(IXMLRPCHandler)\n"
        "    def xmlrpc_namespace(self):\n"
        "        return 'test_unichr'\n"
        "    def xmlrpc_methods(self):\n"
        "        yield ('XML_RPC', ((str, int),), self.unichr)\n"
        "    def unichr(self, req, code):\n"
        "        return (r'\U%08x' % code).decode('unicode-escape')\n")
        rpc_testenv.restart()

        from tracrpc.xml_rpc import _illegal_unichrs, REPLACEMENT_CHAR

        for low, high in _illegal_unichrs:
            for x in (low, (low + high) / 2, high):
                self.assertEquals(REPLACEMENT_CHAR,
                                  self.user.test_unichr.unichr(x),
                                  "Failed unichr with U+%04X" % (x,))

        # surrogate pair on narrow build
        self.assertEquals(u'\U0001D4C1', self.user.test_unichr.unichr(0x1D4C1))

        # Remove plugin and restart
        os.unlink(plugin)
        rpc_testenv.restart()

def test_suite():
    return unittest.makeSuite(RpcXmlTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
