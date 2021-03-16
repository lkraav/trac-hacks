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
from subversioncli.svn_cli import SubversionCliChangeset, SubversionRepositoryCli

if repo_url.startswith('http'):
    url = '/' + repo_url
else:
    url = '/' + repo_url[6:].lstrip('/')

class TestSvnCliChangeset(unittest.TestCase):

    @staticmethod
    def _log(msg):
        print(msg)

    def setUp(self):
        self.log = Mock(info=self._log, error=self._log, debug=self._log)
        self.repos = Mock(repo_url=url, log=self.log)
        parms = {'name': 'Test-Repo', 'id': 1}
        if url.startswith('/http'):
            parms['type'] = 'svn-cli-remote'
        else:
            parms['type'] = 'svn-cli-direct'

        self.repos = SubversionRepositoryCli(url, parms, self.log)

    def test_changeset_get_changes_11177(self):
        expected = [(u'/customfieldadminplugin/0.11/customfieldadmin/admin.py', 'file', 'move',
                     u'/customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 11170),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/api.py', 'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/api.py', 11168),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/locale/customfieldadmin.pot', 'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/locale/customfieldadmin.pot', 11168),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/locale/ja/LC_MESSAGES/customfieldadmin.po',
                     'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/locale/ja/LC_MESSAGES/customfieldadmin.po', 11171),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/locale/nb/LC_MESSAGES/customfieldadmin.po',
                     'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/locale/nb/LC_MESSAGES/customfieldadmin.po', 11168),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/locale/ru/LC_MESSAGES/customfieldadmin.po',
                     'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/locale/ru/LC_MESSAGES/customfieldadmin.po', 11168),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/templates/customfieldadmin.html', 'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/templates/customfieldadmin.html', 11168),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/tests/__init__.py', 'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/tests/__init__.py', 11168),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/tests/admin.py', 'file', 'move',
                     u'/customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py', 11170),
                    (u'/customfieldadminplugin/0.11/customfieldadmin/tests/api.py', 'file', 'edit',
                     u'/customfieldadminplugin/0.11/customfieldadmin/tests/api.py', 11168),
                    (u'/customfieldadminplugin/0.11/setup.py', 'file', 'edit',
                     u'/customfieldadminplugin/0.11/setup.py', 11168)
                   ]
        rev = 11177
        changeset = SubversionCliChangeset(self.repos, rev)
        self.assertIsInstance(changeset, SubversionCliChangeset)
        changes = list(changeset.get_changes())
        # get_changeset_info() for this changeset returns 13. But we have 2 * svn-move in the changeset
        # and svn shows one ADD for the destination and one DELETE for the source of every move.
        self.assertEqual(11, len(changes))
        for idx, change in enumerate(changes):
            self.assertSequenceEqual(expected[idx], change)

    def test_changeset_get_changes_18045(self):

        # This changeset is interesting because it contains some svn-copy action and some
        # files (e.g. '/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/smp_model.py')
        # have action='R' (replace).

        # '/simplemultiprojectplugin/tags/smp-0.7.3/setup.cfg' is esp. interesting because this file
        # was edited in the working copy of 'trunk'. After that the working copy was tagged as
        # smp-0.7.3 (which is svn-copy in reality).
        # In the 'svn log' the file shows up as just edited but not as copied. An older
        # version does not exist in the new path. So the Trac diff must use the old path in trunk
        # which means we need some special handling..
        expected = [(u'/simplemultiprojectplugin/tags/smp-0.7.3', 'dir', 'copy', u'/simplemultiprojectplugin/trunk', 18042),
                    (u'/simplemultiprojectplugin/tags/smp-0.7.3/setup.cfg', 'file', 'edit', u'/simplemultiprojectplugin/trunk/setup.cfg', 17989),
                    (u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/query.py', 'file', 'add', None, -1),
                    (u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/smp_model.py', 'file', 'copy', u'/simplemultiprojectplugin/trunk/simplemultiproject/smp_model.py', 18044),
                    (u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_environment_setup.py', 'file', 'copy', u'/simplemultiprojectplugin/trunk/simplemultiproject/tests/test_environment_setup.py', 18043),
                    (u'/simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_smpproject.py', 'file', 'copy', u'/simplemultiprojectplugin/trunk/simplemultiproject/tests/test_smpproject.py', 18044)
                    ]
        rev = 18045
        changeset = SubversionCliChangeset(self.repos, rev)
        self.assertIsInstance(changeset, SubversionCliChangeset)
        changes = list(changeset.get_changes())
        self.assertEqual(6, len(changes))
        for idx, change in enumerate(changes):
            self.assertSequenceEqual(expected[idx], change)


if __name__ == '__main__':
    unittest.main()
