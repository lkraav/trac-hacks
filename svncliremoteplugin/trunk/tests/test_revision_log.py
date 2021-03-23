import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionCliNode, SubversionCliRepository


class TestRevisionLog(unittest.TestCase):
    """Revision log uses data gathered with Node.get_history()"""

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
        self.repos = SubversionCliRepository(self.url, parms, self.log)

    def test_revision_log(self):
        """Test getting a revision log"""
        path = 'peerreviewplugin/trunk/codereview/changeset.py'
        rev = 18046
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path, node.path)
        history = list(node.get_history())
        self.assertEqual(3, len(history))

    def test_revision_log_11190(self):
        """Test getting a revision log for a file with several copy operations."""
        # The file was created with 2250, copied in 2388 and again 11177
        # and modified in between up to 11187. Next change was in 11198
        path = 'customfieldadminplugin/0.11/customfieldadmin/admin.py'
        rev = 11190
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path, node.path)
        history = list(node.get_history())
        self.assertEqual(18, len(history))

        expected = [(u'customfieldadminplugin/0.11/customfieldadmin/admin.py', 11187, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/admin.py', 11177, 'copy'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 11168, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 11149, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 10368, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 8782, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 6485, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 6469, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 5252, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 5236, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 5161, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 5032, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 4964, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 4016, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 2652, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 2389, 'edit'),
                    (u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 2388, 'copy'),
                    (u'customfieldadminplugin/0.10/customfieldadmin/customfieldadmin.py', 2250, 'add')
                    ]
        for idx, item in enumerate(history):
            self.assertSequenceEqual(expected[idx], item)

    def test_revision_log_1984(self):
        """Test getting a rvision log (history)"""
        path = 'htgroupsplugin/trunk/htgroups/__init__.py'
        rev = 1984
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path, node.path)
        history = list(node.get_history())
        self.assertEqual(3, len(history))

        expected = [(u'htgroupsplugin/trunk/htgroups/__init__.py', 1984, 'copy'),
                    (u'htgroupsplugin/0.9/htgroups/__init__.py', 399, 'edit'),
                    (u'htgroupsplugin/0.9/htgroups/__init__.py', 398, 'add')
                    ]
        for idx, item in enumerate(history):
            self.assertSequenceEqual(expected[idx], item)

    def test_revision_log_200_file_escape_char(self):
        """Revision log for a file with escape character"""
        rev = 200
        path = u'graphvizplugin/branches/v0.5/examples/GraphvizExamples%2FWikiLinks'
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path, node.path)
        history = list(node.get_history())
        self.assertEqual(1, len(history))

        expected = [(u'graphvizplugin/branches/v0.5/examples/GraphvizExamples%2FWikiLinks', 200, 'add')]
        for idx, item in enumerate(history):
            self.assertSequenceEqual(expected[idx], item)


class TestRevisionLogSubtree(unittest.TestCase):
    """Revision log uses data gathered with Node.get_history()"""

    tst_repo = 'https://trac-hacks.org/svn/peerreviewplugin'

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
        self.repos = SubversionCliRepository(self.url, parms, self.log)

    def test_revision_log(self):
        """Test getting a file node"""
        path = 'peerreviewplugin/trunk/codereview/changeset.py'
        path_normalized = 'trunk/codereview/changeset.py'
        rev = 18046
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path_normalized, node.path)
        history = list(node.get_history())
        self.assertEqual(3, len(history))


if __name__ == '__main__':
    unittest.main()
