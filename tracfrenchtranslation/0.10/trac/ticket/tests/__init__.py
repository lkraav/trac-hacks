import unittest

from trac.ticket.tests import api, model, query, wikisyntax, notification, \
                              conversion

def suite():
    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    suite.addTest(model.suite())
    suite.addTest(query.suite())
    suite.addTest(wikisyntax.suite())
    suite.addTest(notification.suite())
    suite.addTest(conversion.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
