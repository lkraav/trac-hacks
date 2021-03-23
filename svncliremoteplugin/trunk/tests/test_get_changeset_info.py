# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import unittest

from tests import repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionCliRepository
from subversioncli.svn_client import get_changeset_info


class TestGetChangesetInfo(unittest.TestCase):

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

    def test_get_changeset_info_11177(self):
        expected = {u'/customfieldadminplugin/0.11/customfieldadmin/api.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/admin.py':
                        {'copyfrom-path': u'/customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py',
                         'kind': u'file', 'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': u'11170', 'action': u'A'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/api.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/templates/customfieldadmin.html':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/admin.py':
                        {'copyfrom-path': u'/customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py',
                         'kind': u'file', 'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': u'11170', 'action': u'A'},
                    u'/customfieldadminplugin/0.11/setup.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'false', 'rev': 11177, 'copyfrom-rev': '', 'action': u'D'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/__init__.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/customfieldadmin.pot':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'false', 'rev': 11177, 'copyfrom-rev': '', 'action': u'D'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/nb/LC_MESSAGES/customfieldadmin.po':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/ru/LC_MESSAGES/customfieldadmin.po':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/ja/LC_MESSAGES/customfieldadmin.po':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'}}

        rev = 11177
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(13, len(changes))
        for change in changes:
            attrs, path = change
            self.assertEqual(expected[path]['copyfrom-path'], attrs['copyfrom-path'])
            self.assertEqual(expected[path]['copyfrom-rev'], attrs['copyfrom-rev'])
            self.assertEqual(expected[path]['kind'], attrs['kind'])
            self.assertEqual(expected[path]['rev'], attrs['rev'])
            self.assertEqual(expected[path]['action'], attrs['action'])

    def test_get_changeset_info_18045(self):
        expected = {u'/simplemultiprojectplugin/tags/smp-0.7.3/setup.cfg':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 18045, 'copyfrom-rev': '', 'action': u'M'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/query.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 18045, 'copyfrom-rev': '', 'action': u'A'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/smp_model.py':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk/simplemultiproject/smp_model.py',
                         'kind': u'file', 'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18044', 'action': u'R'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_environment_setup.py':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk/simplemultiproject/tests/test_environment_setup.py',
                         'kind': u'file', 'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18043', 'action': u'R'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk', 'kind': u'dir',
                         'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18042', 'action': u'A'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_smpproject.py':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk/simplemultiproject/tests/test_smpproject.py',
                         'kind': u'file', 'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18044', 'action': u'R'}
                    }

        rev = 18045
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(6, len(changes))
        for change in changes:
            attrs, path = change
            self.assertEqual(expected[path]['copyfrom-path'], attrs['copyfrom-path'])
            self.assertEqual(expected[path]['copyfrom-rev'], attrs['copyfrom-rev'])
            self.assertEqual(expected[path]['kind'], attrs['kind'])
            self.assertEqual(expected[path]['rev'], attrs['rev'])
            self.assertEqual(expected[path]['action'], attrs['action'])

    def test_get_changeset_info_16400(self):
        """Test changeset with deleted directories"""
        expected = {u'/bittenforgitplugin/0.11/0.6b2':
                        {'copyfrom-path': '', 'kind': u'dir',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': '', 'action': u'D'},
                    u'/bittenforgitplugin/0.11/setup.cfg':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/setup.cfg', 'kind': u'file',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/bitten/build':
                        {'copyfrom-path': '', 'kind': u'dir',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': '', 'action': u'D'},
                    u'/bittenforgitplugin/0.11/MANIFEST.in':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/MANIFEST.in', 'kind': u'file',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/COPYING':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/COPYING', 'kind': u'file',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/setup.py':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/setup.py', 'kind': u'file',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/doc':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/doc', 'kind': u'dir',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/README.txt':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/README.txt', 'kind': u'file',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/ChangeLog':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/ChangeLog', 'kind': u'file',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/bitten':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/bitten', 'kind': u'dir',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'},
                    u'/bittenforgitplugin/0.11/MANIFEST-SLAVE.in':
                        {'copyfrom-path': u'/bittenforgitplugin/0.11/0.6b2/MANIFEST-SLAVE.in', 'kind': u'file',
                         'text-mods': u'false', 'rev': 16400, 'copyfrom-rev': u'16399', 'action': u'A'}
                    }

        rev = 16400
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(11, len(changes))
        for change in changes:
            attrs, path = change
            self.assertEqual(expected[path]['copyfrom-path'], attrs['copyfrom-path'])
            self.assertEqual(expected[path]['copyfrom-rev'], attrs['copyfrom-rev'])
            self.assertEqual(expected[path]['kind'], attrs['kind'])
            self.assertEqual(expected[path]['rev'], attrs['rev'])
            self.assertEqual(expected[path]['action'], attrs['action'])

    def test_get_changeset_info_399(self):
        rev = 399
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(9, len(changes))

    def test_get_changeset_info_200(self):
        expected = {u'/graphvizplugin/branches/v0.5/examples/GraphvizExamples':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 200, 'copyfrom-rev': '', 'action': u'M'},
                    u'/graphvizplugin/branches/v0.5/examples/GraphvizExamples%2FWikiLinks':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 200, 'copyfrom-rev': '', 'action': u'A'},
                    u'/graphvizplugin/branches/v0.5/graphviz/graphviz.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 200, 'copyfrom-rev': '', 'action': u'M'}
                    }
        rev = 200
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(3, len(changes))
        for change in changes:
            attrs, path = change
            self.assertEqual(expected[path]['copyfrom-path'], attrs['copyfrom-path'])
            self.assertEqual(expected[path]['copyfrom-rev'], attrs['copyfrom-rev'])
            self.assertEqual(expected[path]['kind'], attrs['kind'])
            self.assertEqual(expected[path]['rev'], attrs['rev'])
            self.assertEqual(expected[path]['action'], attrs['action'])

    def test_get_changeset_info_1066(self):
        expected = {u'/graphvizplugin/branches/v0.5/examples/GraphvizExamples':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 200, 'copyfrom-rev': '', 'action': u'M'},
                    u'/graphvizplugin/branches/v0.5/examples/GraphvizExamples%2FWikiLinks':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 200, 'copyfrom-rev': '', 'action': u'A'},
                    u'/graphvizplugin/branches/v0.5/graphviz/graphviz.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 200, 'copyfrom-rev': '', 'action': u'M'}
                    }
        rev = 1066
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(17, len(changes))


class TestGetChangesetInfoSubtree(unittest.TestCase):

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
        self.repos = SubversionCliRepository(self.url, parms, self.log)

    def test_get_changeset_info_11177(self):
        # Note that the path is *not* normalized here!
        expected = {u'/customfieldadminplugin/0.11/customfieldadmin/api.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/admin.py':
                        {'copyfrom-path': u'/customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py',
                         'kind': u'file', 'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': u'11170', 'action': u'A'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/api.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/templates/customfieldadmin.html':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/admin.py':
                        {'copyfrom-path': u'/customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py',
                         'kind': u'file', 'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': u'11170', 'action': u'A'},
                    u'/customfieldadminplugin/0.11/setup.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'false', 'rev': 11177, 'copyfrom-rev': '', 'action': u'D'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/tests/__init__.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/customfieldadmin.pot':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'false', 'rev': 11177, 'copyfrom-rev': '', 'action': u'D'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/nb/LC_MESSAGES/customfieldadmin.po':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/ru/LC_MESSAGES/customfieldadmin.po':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'},
                    u'/customfieldadminplugin/0.11/customfieldadmin/locale/ja/LC_MESSAGES/customfieldadmin.po':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 11177, 'copyfrom-rev': '', 'action': u'M'}}

        rev = 11177
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(13, len(changes))
        for change in changes:
            attrs, path = change
            self.assertEqual(expected[path]['copyfrom-path'], attrs['copyfrom-path'])
            self.assertEqual(expected[path]['copyfrom-rev'], attrs['copyfrom-rev'])
            self.assertEqual(expected[path]['kind'], attrs['kind'])
            self.assertEqual(expected[path]['rev'], attrs['rev'])
            self.assertEqual(expected[path]['action'], attrs['action'])

    def test_get_changeset_info_18045(self):
        expected = {u'/simplemultiprojectplugin/tags/smp-0.7.3/setup.cfg':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 18045, 'copyfrom-rev': '', 'action': u'M'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/query.py':
                        {'copyfrom-path': '', 'kind': u'file',
                         'text-mods': u'true', 'rev': 18045, 'copyfrom-rev': '', 'action': u'A'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/smp_model.py':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk/simplemultiproject/smp_model.py',
                         'kind': u'file', 'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18044', 'action': u'R'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_environment_setup.py':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk/simplemultiproject/tests/test_environment_setup.py',
                         'kind': u'file', 'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18043', 'action': u'R'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk', 'kind': u'dir',
                         'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18042', 'action': u'A'},
                    u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_smpproject.py':
                        {'copyfrom-path': u'/simplemultiprojectplugin/trunk/simplemultiproject/tests/test_smpproject.py',
                         'kind': u'file', 'text-mods': u'false', 'rev': 18045, 'copyfrom-rev': u'18044', 'action': u'R'}
                    }

        rev = 18045
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(6, len(changes))
        for change in changes:
            attrs, path = change
            self.assertEqual(expected[path]['copyfrom-path'], attrs['copyfrom-path'])
            self.assertEqual(expected[path]['copyfrom-rev'], attrs['copyfrom-rev'])
            self.assertEqual(expected[path]['kind'], attrs['kind'])
            self.assertEqual(expected[path]['rev'], attrs['rev'])
            self.assertEqual(expected[path]['action'], attrs['action'])

    def test_get_changeset_info_399(self):
        rev = 399
        change_tuple = get_changeset_info(self.repos, rev)
        self.assertEqual(3, len(change_tuple))  # [path_entry 1, path_Entry 2, ...], [copy 1, copy 2, ...]
        changes, copied, deleted = change_tuple
        self.assertEqual(9, len(changes))


if __name__ == '__main__':
    unittest.main()
