'''
Created on 12.09.2014

@author: franz.mayer
'''
import getpass
import os
import shutil
import tempfile
import unittest

from logwatcher import api
from trac.test import EnvironmentStub


usrname = getpass.getuser()
usrtemppath = os.environ['TEMP']


class TestApi(unittest.TestCase):
    params = dict()

    @classmethod
    def setUpClass(self, port=None):
        super(TestApi, self).setUpClass()
        self.env = EnvironmentStub(enable=[
            'trac.*', 'logwatcher.api'
        ])

        if not os.path.isdir(usrtemppath + "/TempLog"):
            os.mkdir(usrtemppath + "/TempLog")
        self.env.path = tempfile.mkdtemp(dir=usrtemppath + "/TempLog")

        os.mkdir('%s/log' % self.env.path)
        self.env.config.set('logging', 'log_type', 'file')
        self.env.config.set('logging', 'log_level', 'INFO')
        self.env.setup_log()
        # print 'successfully set up with env path: %s' % self.env.path

        test_api = api.LogViewerApi(self.env)
        test_api.log.info('*** INFO ***')
        test_api.log.info('DeBug : Data could not be found')
        test_api.log.info('DEBUG: Processing form data')
        test_api.log.info('Error: Lost Connection data to Server ')

        self.params['sensitive'] = None
        self.params['tail'] = "100"
        self.params['up'] = 0
        self.params['invert'] = None
        self.params['regexp'] = None
        self.params['level'] = 0
        self.params['extlines'] = 0

    def test_get_logfile_name(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()
        print "log file name: %s" % logfile_name
        self.assertIsNotNone(logfile_name, "log file name is None")

    def test_get_log_settings_default(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()

        self.params['filter'] = "startup"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 1, "The amount of found words are wrong")

    def test_get_log_settings_sensitive(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()
        self.params['invert'] = None
        self.params['sensitive'] = '1'

        self.params['filter'] = "DEBUG"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 1, "The amount of found words are wrong")

        self.params['filter'] = "Debug"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log == [], "Could not find Word")
        self.assertEquals(len(log), 0, "The amount of found words are wrong")

    def test_get_log_settings_sensitive_invert(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()
        self.params['sensitive'] = '1'
        self.params['invert'] = '1'

        self.params['filter'] = "startup"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 4, "The amount of found words are wrong")

    def test_get_log_settings_invert(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()

        self.params['sensitive'] = None
        self.params['invert'] = "1"

        self.params['filter'] = "Debug"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 3, "The amount of found words are wrong")

    def test_get_log_settings_regexp_sensitive(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()
        self.params['sensitive'] = '1'
        self.params['regexp'] = '1'
        self.params['invert'] = None

        self.params['filter'] = "data$"
        log = test_api.get_log(logfile_name, self.params)

        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 1, "The amount of found words are wrong")

        self.params['filter'] = "Data$"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log == [], "Could not find Word")
        self.assertEquals(len(log), 0, "The amount of found words are wrong")

    def test_get_log_settings_regexp_insensitive(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()

        self.params['sensitive'] = None
        self.params['regexp'] = '1'
        self.params['invert'] = None
        self.params['filter'] = "Data$"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 1, "The amount of found words are wrong")

    def test_get_log_settings_regexp_sensitive_invert(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()

        self.params['sensitive'] = '1'
        self.params['invert'] = '1'
        self.params['regexp'] = '1'

        self.params['filter'] = "data$"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 4, "The amount of found words are wrong")

        self.params['filter'] = "Data$"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 5, "The amount of found words are wrong")

    def test_get_log_settings_regexp_insensitive_invert(self):
        test_api = api.LogViewerApi(self.env)
        logfile_name = test_api.get_logfile_name()

        self.params['sensitive'] = None
        self.params['invert'] = '1'
        self.params['regexp'] = '1'

        self.params['filter'] = "DAta$"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 4, "The amount of found words are wrong")
        self.params['filter'] = "data$"
        log = test_api.get_log(logfile_name, self.params)
        self.assert_(log != [], "Could not find Word")
        self.assertEquals(len(log), 4, "The amount of found words are wrong")

    @classmethod
    def tearDownClass(self):
        super(TestApi, self).tearDownClass()
        dirPath = usrtemppath + "/TempLog"
        self.env.shutdown()
        shutil.rmtree(dirPath)


def suite():
    print "Starting **API** test suite"
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestApi, 'test'))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
