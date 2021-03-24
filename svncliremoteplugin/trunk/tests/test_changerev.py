import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionCliRepository
from subversioncli.svn_client import get_change_rev


class TestCangeRevison(unittest.TestCase):
    """Test function get_change_rev()"""

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
        self.path = path = 'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py'

    def test_chgrev_is_currev(self):
        """Check for correct change revision when change rev is the current revision"""
        self.assertEqual(11168, get_change_rev(self.repos, 11168, self.path))

    def test_chgrev_is_not_currev(self):
        """Check for correct change revision when change rev is *not* the current revision"""
        self.assertEqual(11168, get_change_rev(self.repos, 11170, self.path))


class TestCangeRevisonSubtree(unittest.TestCase):
    """Test function get_change_rev() for a repo pointing to a subtree"""

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
        self.path = 'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py'

    def test_chgrev_is_currev(self):
        """Check for correct change revision when change rev is the current revision"""
        self.assertEqual(11168, get_change_rev(self.repos, 11168, self.path))

    def test_chgrev_is_not_currev(self):
        """Check for correct change revision when change rev is *not* the current revision"""
        path = 'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py'
        # The path is normalized in the node. So we do it here, too.
        self.assertEqual(11168, get_change_rev(self.repos, 11170, path))


if __name__ == '__main__':
    unittest.main()
