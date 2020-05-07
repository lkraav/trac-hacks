
from unittest import TestCase, TestSuite, makeSuite

from trac.perm import DefaultPermissionStore
from trac.test import EnvironmentStub

from tracfullblog.db import FullBlogSetup


class FullBlogTestCaseTemplate(TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=['trac.*', 'tracfullblog.*'])
        FullBlogSetup(self.env).upgrade_environment()
        # permissions
        self.env.config.set('trac', 'permission_store',
                            'DefaultPermissionStore')
        self.env.config.set('trac', 'permission_policies',
                            'DefaultPermissionPolicy')

    def tearDown(self):
        self.env.destroy_db()
        del self.env


def test_suite():
    suite = TestSuite()
    import tracfullblog.tests.core
    suite.addTest(tracfullblog.tests.core.test_suite())
    import tracfullblog.tests.model
    suite.addTest(tracfullblog.tests.model.test_suite())
    import tracfullblog.tests.web_ui
    suite.addTest(tracfullblog.tests.web_ui.test_suite())
    return suite
