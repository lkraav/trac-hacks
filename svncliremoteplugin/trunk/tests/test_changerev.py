import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_client import get_change_rev


class TestCangeRevison(unittest.TestCase):
    """Test function get_change_rev()"""

    def setUp(self):
        self.repos = Mock(repo_url=repo_url)
        self.path = path = 'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py'

    def test_chgrev_is_currev(self):
        """Check for correct change revision when change rev is the current revision"""
        self.assertEqual(11168, get_change_rev(self.repos, 11168, self.path))

    def test_chgrev_is_not_currev(self):
        """Check for correct change revision when change rev is *not* the current revision"""
        self.assertEqual(11168, get_change_rev(self.repos, 11170, self.path))


if __name__ == '__main__':
    unittest.main()
