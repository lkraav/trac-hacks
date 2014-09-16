'''
Created on 12.09.2014

@author: franz.mayer
'''
import unittest
from logwatcher import api
from trac.test import EnvironmentStub
import tempfile
import os


class TestApi(unittest.TestCase):

    def setUp(self, port=None):
        self.env = EnvironmentStub(enable=[
            'trac.*', 'logwatcher.api'
        ])
        self.env.path = tempfile.mkdtemp()
        os.mkdir('%s/log' % self.env.path)

        self.env.config.set('logging', 'log_type', 'file')
        self.env.setup_log()
        print 'successfully set up with env path: %s' % self.env.path

    def test_get_logfile_name(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()
        print "log file name: %s" % logfile_name
        self.assertIsNotNone(logfile_name, "log file name is None")


def suite():
    print "Starting **API** test suite"
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestApi, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
