import unittest

import os
from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import repo_url_from_path, SubversionCliRepository
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
        parms = {'name': 'Test-Repo', 'id': 1,
                 'type': 'svn-cli-direct'}
        self.repos = SubversionCliRepository(self.url, parms, self.log)

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
        parms = {'name': 'Test-Repo', 'id': 1,
                 'type': 'svn-cli-direct'}
        self.repos = SubversionCliRepository(self.url, parms, self.log)

    def test_get_rev_info(self):
        info = self.repos.get_rev_info(17788)
        # If a revision can't be found the date is set to None
        self.assertIsNotNone(info[1])


class TestRepoUrlFromPath(unittest.TestCase):

    def setUp(self):
        self.old_os = os.name

    def tearDown(self):
        os.name = self.old_os

    def test_init_svn_cli_file(self):
        os.name = 'posix'
        path = '/path/to/repo'
        url = repo_url_from_path(path)
        self.assertEqual('file:///path/to/repo', url)

    def test_init_svn_cli_http(self):
        os.name = 'posix'
        paths = ['/http://path/to/repo', '/https://path/to/repo']
        url = repo_url_from_path(paths[0])
        self.assertEqual('http://path/to/repo', url)

        url = repo_url_from_path(paths[1])
        self.assertEqual('https://path/to/repo', url)

    def test_init_svn_cli_nt_file(self):
        os.name = 'nt'
        path = 'x:/path/to/repo'
        url = repo_url_from_path(path)
        self.assertEqual('file:///x:/path/to/repo', url)

    def test_init_svn_cli_nt_http(self):
        os.name = 'nt'
        paths = ['x:/http://path/to/repo', 'x:/https://path/to/repo']
        url = repo_url_from_path(paths[0])
        self.assertEqual('http://path/to/repo', url)

        url = repo_url_from_path(paths[1])
        self.assertEqual('https://path/to/repo', url)


if __name__ == '__main__':
    unittest.main()
