import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionRepositoryCli
from subversioncli.svn_client import list_path


class TestListPath(unittest.TestCase):
    """Test function list_path() in svn_client.py"""

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

    def test_list_path(self):
        expected = [(u'customfieldadminplugin/0.11/customfieldadmin/__init__.py', (133, 11198)),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py', (5942, 17541)),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py', (10262, 17540)),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs', (None, u'5253')),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs/locale', (None, u'16679')),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs/locale/templates', (None, u'13289')),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs/locale/templates/tests', (None, u'16677'))]
        path = 'customfieldadminplugin/0.11/customfieldadmin'
        rev = 18046
        res = list_path(self.repos, rev, path)
        self.assertEqual(7, len(res))
        for idx, item in enumerate(res):
            self.assertSequenceEqual(expected[idx], item)


class TestListPathSubtree(unittest.TestCase):
    """Test function list_path() in svn_client.py"""

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

    def test_list_path(self):
        expected = [(u'customfieldadminplugin/0.11/customfieldadmin/__init__.py', (133, 11198)),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py', (5942, 17541)),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py', (10262, 17540)),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs', (None, u'5253')),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs/locale', (None, u'16679')),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs/locale/templates', (None, u'13289')),
                    (u'customfieldadminplugin/0.11/customfieldadmin/__init__.py/admin.py/api.py/htdocs/locale/templates/tests', (None, u'16677'))]
        path = 'customfieldadminplugin/0.11/customfieldadmin'  # Path must be normalized
        rev = 18046
        res = list_path(self.repos, rev, path)
        self.assertEqual(7, len(res))
        for idx, item in enumerate(res):
            self.assertSequenceEqual(expected[idx], item)


if __name__ == '__main__':
    unittest.main()
