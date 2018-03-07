import unittest

from simplemultiproject.tests import test_session, test_smpcomponent, \
                                     test_smpmilestone, test_smpversion


def suite():
    suite = unittest.TestSuite()
    suite.addTest(test_session.suite())
    suite.addTest(test_smpcomponent.suite())
    suite.addTest(test_smpmilestone.suite())
    suite.addTest(test_smpversion.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
