
from unittest import TestSuite, makeSuite

def test_suite():
    suite = TestSuite()
    import tracfullblog.tests.model
    suite.addTest(makeSuite(tracfullblog.tests.model.GroupPostsByMonthTestCase))
    return suite
