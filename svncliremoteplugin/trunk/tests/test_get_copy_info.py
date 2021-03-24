import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionCliRepository
from subversioncli.svn_client import get_copy_info


class TestGetCopyInfo(unittest.TestCase):
    """Test function get_copy_info() in svn_client.py"""

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

    def test_copy_info_1000(self):
        res = get_copy_info(self.repos, 1000)
        self.assertEqual(211, len(res))


class TestGetCopyInfoSubtree(unittest.TestCase):
    """Test function get_copy_info() in svn_client.py"""

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

    def test_copy_info_1000(self):
        res = get_copy_info(self.repos, 1000)
        self.assertEqual(211, len(res))


if __name__ == '__main__':
    unittest.main()
