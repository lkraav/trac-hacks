import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionCliNode, SubversionCliRepository
from subversioncli.svn_client import get_history


class TestGetHistory(unittest.TestCase):
    """Test function get_history() in svn_client.py"""

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

    def test_get_history_11177(self):
        """The path was copied in revision 11177 from another/path@11168"""
        res = [(u'customfieldadminplugin/0.11/customfieldadmin/admin.py', 11177, 'copy'),
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
               (u'customfieldadminplugin/0.10/customfieldadmin/customfieldadmin.py', 2250, 'add'),
               ]
        path = 'customfieldadminplugin/0.11/customfieldadmin/admin.py'
        rev = 11177
        node = SubversionCliNode(self.repos, path, rev, self.log)
        history = get_history(self.repos, rev, node.path)
        self.assertEqual(17, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)

    def test_get_history_3342(self):
        """"""
        res = [(u'simpleticketplugin/0.11/simpleticket/web_ui.py', 3342, 'edit'),
               (u'simpleticketplugin/0.11/simpleticket/web_ui.py', 3340, 'copy'),
               (u'simpleticketplugin/0.10/simpleticket/web_ui.py', 1545, 'edit'),
               (u'simpleticketplugin/0.10/simpleticket/web_ui.py', 1332, 'edit'),
               (u'simpleticketplugin/0.10/simpleticket/web_ui.py', 1307, 'edit'),
               (u'simpleticketplugin/0.10/simpleticket/web_ui.py', 1148, 'edit'),
               (u'simpleticketplugin/0.10/simpleticket/web_ui.py', 1147, 'copy'),
               (u'simpleticketplugin/0.9/simpleticket/web_ui.py', 1002, 'edit'),
               (u'simpleticketplugin/0.9/simpleticket/web_ui.py', 997, 'add')]

        path = u'simpleticketplugin/0.11/simpleticket/web_ui.py'
        rev = 3342
        node = SubversionCliNode(self.repos, path, 3342, self.log)
        history = get_history(self.repos, rev, node.path)
        self.assertEqual(9, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)

    def test_get_history_16400(self):
        """This directory is deleted"""
        res = [(u'bittenforgitplugin/0.11/setup.py', 16400, 'copy'),
               (u'bittenforgitplugin/0.11/0.6b2/setup.py', 8507, 'add')]

        path = u'bittenforgitplugin/0.11/setup.py'
        rev = 16400
        node = SubversionCliNode(self.repos, path, 16400, self.log)
        history = get_history(self.repos, rev, node.path)
        self.assertEqual(2, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)

    def test_get_history_200(self):
        """File with several consecutive copies."""
        # The file was created with 189, copied in 193, 194 and 196
        # and modified in 200.
        res = [(u'graphvizplugin/branches/v0.5/examples/GraphvizExamples', 200, 'edit'),
               (u'graphvizplugin/branches/v0.5/examples/GraphvizExamples', 196, 'copy'),
               (u'graphvizplugin/branches/0.9/v0.5/examples/GraphvizExamples', 194, 'copy'),
               (u'graphvizplugin/0.9/examples/GraphvizExamples', 193, 'copy'),
               (u'graphvizplugin/branches/0.9/v0.4/examples/GraphvizExamples', 189, 'add')
               ]
        rev = 200
        path = u'graphvizplugin/branches/v0.5/examples/GraphvizExamples'
        node = SubversionCliNode(self.repos, path, rev, self.log)
        history = get_history(self.repos, rev, node.path)
        self.assertEqual(5, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)

    def test_get_history_200_file_escape_char(self):
        """File with escape character '%2F' in the name."""
        res = [(u'graphvizplugin/branches/v0.5/examples/GraphvizExamples%2FWikiLinks', 200, 'add')]
        rev = 200
        path = u'graphvizplugin/branches/v0.5/examples/GraphvizExamples%2FWikiLinks'
        node = SubversionCliNode(self.repos, path, rev, self.log)
        history = get_history(self.repos, rev, node.path)
        self.assertEqual(1, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)


class TestGetHistorySubtree(unittest.TestCase):
    """Test function get_history() in svn_client.py"""

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

    def test_get_history_11177(self):
        """The path was copied in revision 11177 from another/path@11168"""
        res = [(u'customfieldadminplugin/0.11/customfieldadmin/admin.py', 11177, 'copy'),
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
               (u'customfieldadminplugin/0.10/customfieldadmin/customfieldadmin.py', 2250, 'add'),
               ]
        path = 'customfieldadminplugin/0.11/customfieldadmin/admin.py'
        rev = 11177
        node = SubversionCliNode(self.repos, path, 11177, self.log)
        history = get_history(self.repos, rev, node.path)
        self.assertEqual(17, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)


if __name__ == '__main__':
    unittest.main()
