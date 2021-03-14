import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_client import get_history


class TestGetHistory(unittest.TestCase):
    """Test function get_history() in svn_client.py"""

    @staticmethod
    def _log(msg):
        print(msg)

    def setUp(self):
        self.repos = Mock(repo_url=repo_url, log=Mock(info=self._log))

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
        history = get_history(self.repos, 11177, path)
        self.assertEqual(17, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)

    def test_get_history_3342(self):
        """The path was copied in revision 11177 from another/path@11168"""
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
        history = get_history(self.repos, 3342, path)
        self.assertEqual(9, len(history))
        for idx, item in enumerate(history):
            self.assertSequenceEqual(res[idx], item)


if __name__ == '__main__':
    unittest.main()
