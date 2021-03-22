import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionRepositoryCli
from subversioncli.svn_client import get_change_rev


class TestSvnCliRepository(unittest.TestCase):

    if repo_url.startswith('http'):
        url = '/' + repo_url
    else:
        url = '/' + repo_url[6:].lstrip('/')

    @staticmethod
    def _log(msg):
        print(msg)

    def setUp(self):
        self.log = Mock(info=self._log, debug=self._log, error=self._log)
        parms = {'name': 'Test-Repo', 'id': 1}
        if self.url.startswith('/http'):
            parms['type'] = 'svn-cli-remote'
        else:
            parms['type'] = 'svn-cli-direct'
        self.repos = SubversionRepositoryCli(self.url, parms, self.log)

    def test_get_rev_info(self):
        info = self.repos.get_rev_info(17788)
        self.assertIsNotNone(info[1])


class TestSvnCliRepositorySubtree(unittest.TestCase):

    tst_repo = 'https://trac-hacks.org/svn/customfieldadminplugin'

    if tst_repo.startswith('http'):
        url = '/' + tst_repo
    else:
        url = '/' + tst_repo[6:].lstrip('/')

    @staticmethod
    def _log(msg):
        print(msg)

    def setUp(self):
        self.log = Mock(info=self._log, debug=self._log, error=self._log)
        parms = {'name': 'Test-Repo', 'id': 1}
        if self.url.startswith('/http'):
            parms['type'] = 'svn-cli-remote'
        else:
            parms['type'] = 'svn-cli-direct'
        self.repos = SubversionRepositoryCli(self.url, parms, self.log)

    def test_get_rev_info(self):
        info = self.repos.get_rev_info(17788)
        # If a revision can't be found the date is set to None
        self.assertIsNotNone(info[1])


if __name__ == '__main__':
    unittest.main()
