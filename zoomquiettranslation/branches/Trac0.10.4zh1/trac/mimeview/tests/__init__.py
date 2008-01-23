from trac.mimeview.tests import api, php

import unittest

def suite():
    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    suite.addTest(php.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
