# -*- coding: utf-8 -*-

import unittest
try:
    from openpyxl.writer.write_only import _openpyxl_shutdown
except ImportError:
    pass
else:
    import atexit
    for index, entry in enumerate(atexit._exithandlers):
        if entry[0] == _openpyxl_shutdown:
            del atexit._exithandlers[index]
    del index, entry
    del _openpyxl_shutdown
    del atexit


def suite():
    from tracexceldownload.tests import ticket
    suite = unittest.TestSuite()
    suite.addTest(ticket.suite())
    return suite
