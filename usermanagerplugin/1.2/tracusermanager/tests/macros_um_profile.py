# -*- coding: utf-8 -*-
#
# Copyright 2008 Optaros, Inc.
#

import unittest

from tracusermanager.profile.macros import MacroArguments


class MacrosTestCase(unittest.TestCase):
    def test_macros_arguments(self):
        test_string = "intVar=10,strVar=balamuc,list=abc\,cucu\,piscot," \
                      "dict={piscina=123\,masca=123}"

        args = MacroArguments(test_string)
        self.assertEquals(args.get_int('intVar'), 10)
        self.assertEquals(args.get('strVar'), 'balamuc')
        self.assertEquals(args.get_list('list'), ['abc', 'cucu', 'piscot'])
        self.assertEquals(args.get_dict('dict'),
                          dict(piscina="123", masca="123"))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MacrosTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
