# -*- coding: utf-8 -*-

import unittest

def suite():
    from tracexceldownload.tests import ticket
    suite = unittest.TestSuite()
    suite.addTest(ticket.suite())
    return suite
