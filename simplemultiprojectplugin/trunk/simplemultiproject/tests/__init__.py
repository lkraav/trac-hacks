import unittest

from simplemultiproject.tests import test_smpcomponent, test_prjlist_prefs, test_project_table, test_session, \
                                     test_smpmilestone, test_smpversion


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(test_session.test_suite())
    suite.addTest(test_smpcomponent.test_suite())
    suite.addTest(test_smpmilestone.test_suite())
    suite.addTest(test_smpversion.test_suite())
    suite.addTest(test_prjlist_prefs.test_suite())
    suite.addTest(test_project_table.test_suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
