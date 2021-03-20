# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import unittest
import datetime

from tests import repo_url
from trac.test import EnvironmentStub, Mock, MockRequest
from trac.util.datefmt import to_datetime
from trac.versioncontrol.api import DbRepositoryProvider, NoSuchChangeset
from trac.versioncontrol.web_ui.changeset import ChangesetModule
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
        self.env = EnvironmentStub(True, ['trac.versioncontrol.*',
                                          'subversioncli.svn_cli.*'])
        self.log = Mock(info=self._log, error=self._log, debug=self._log)
        # self.repos = Mock(repo_url=url, log=self.log)
        parms = {'name': 'Test-Repo', 'id': 1}
        if url.startswith('/http'):
            parms['type'] = 'svn-cli-remote'
        else:
            parms['type'] = 'svn-cli-direct'

        self.repos = SubversionRepositoryCli(url, parms, self.log)

    def test_changeset_get_changes_11177(self):
        expected = [(u'customfieldadminplugin/0.11/customfieldadmin/admin.py', 'file', 'move',
                     u'customfieldadminplugin/0.11/customfieldadmin/customfieldadmin.py', 11170),
                    (u'customfieldadminplugin/0.11/customfieldadmin/api.py', 'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/api.py', 11168),
                    (u'customfieldadminplugin/0.11/customfieldadmin/locale/customfieldadmin.pot', 'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/locale/customfieldadmin.pot', 11168),
                    (u'customfieldadminplugin/0.11/customfieldadmin/locale/ja/LC_MESSAGES/customfieldadmin.po',
                     'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/locale/ja/LC_MESSAGES/customfieldadmin.po', 11171),
                    (u'customfieldadminplugin/0.11/customfieldadmin/locale/nb/LC_MESSAGES/customfieldadmin.po',
                     'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/locale/nb/LC_MESSAGES/customfieldadmin.po', 11168),
                    (u'customfieldadminplugin/0.11/customfieldadmin/locale/ru/LC_MESSAGES/customfieldadmin.po',
                     'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/locale/ru/LC_MESSAGES/customfieldadmin.po', 11168),
                    (u'customfieldadminplugin/0.11/customfieldadmin/templates/customfieldadmin.html', 'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/templates/customfieldadmin.html', 11168),
                    (u'customfieldadminplugin/0.11/customfieldadmin/tests/__init__.py', 'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/tests/__init__.py', 11168),
                    (u'customfieldadminplugin/0.11/customfieldadmin/tests/admin.py', 'file', 'move',
                     u'customfieldadminplugin/0.11/customfieldadmin/tests/web_ui.py', 11170),
                    (u'customfieldadminplugin/0.11/customfieldadmin/tests/api.py', 'file', 'edit',
                     u'customfieldadminplugin/0.11/customfieldadmin/tests/api.py', 11168),
                    (u'customfieldadminplugin/0.11/setup.py', 'file', 'edit',
                     u'customfieldadminplugin/0.11/setup.py', 11168)
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
        expected = [(u'simplemultiprojectplugin/tags/smp-0.7.3', 'dir', 'copy', u'simplemultiprojectplugin/trunk', 18042),
                    (u'simplemultiprojectplugin/tags/smp-0.7.3/setup.cfg', 'file', 'edit', u'simplemultiprojectplugin/trunk/setup.cfg', 17989),
                    (u'simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/query.py', 'file', 'add', None, -1),
                    (u'simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/smp_model.py', 'file', 'copy', u'simplemultiprojectplugin/trunk/simplemultiproject/smp_model.py', 18044),
                    (u'simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_environment_setup.py', 'file', 'copy', u'simplemultiprojectplugin/trunk/simplemultiproject/tests/test_environment_setup.py', 18043),
                    (u'simplemultiprojectplugin/tags/smp-0.7.3/simplemultiproject/tests/test_smpproject.py', 'file', 'copy', u'simplemultiprojectplugin/trunk/simplemultiproject/tests/test_smpproject.py', 18044)
                    ]
        rev = 18045
        changeset = SubversionCliChangeset(self.repos, rev)
        self.assertIsInstance(changeset, SubversionCliChangeset)
        changes = list(changeset.get_changes())
        self.assertEqual(6, len(changes))
        for idx, change in enumerate(changes):
            self.assertSequenceEqual(expected[idx], change)

    def test_changeset_get_changeset_17976(self):
        """Check if changeset 17976 raises NoSuchChangeset"""
        # This changeset is empty in 'svn log...'.
        rev = 17976
        self.assertRaises(NoSuchChangeset, SubversionCliChangeset, self.repos, rev)

    def test_changeset_properties_399(self):
        """Check a changeset only containing property changes.
        No content change.

        We call a function in trac.versioncontrol.web_ui.changeset.py which is
        responsible for generating the data for the changeset page.

        NOTE:
        This one may break when someone sets new properties on the whole svn tree
        because this changeset only contains property changes.
        """
        # When not showing a path in the changeset Trac is calling the method
        # with root ('/'), not None or ''.
        path = '/'
        rev = 399
        changeset = SubversionCliChangeset(self.repos, rev)
        self.assertIsInstance(changeset, SubversionCliChangeset)
        changes = list(changeset.get_changes())
        self.assertEqual(9, len(changes))
        cm = ChangesetModule(self.env)

        # Data set in trac.versioncontrol.web_ui.changeset.py -> process_request()
        data = {'repos': self.repos, 'reponame': self.repos.reponame,
                'diff': {'style': u'inline',
                         'options': {'contextall': 1, 'contextlines': 2,
                         'ignorecase': 0,  'ignoreblanklines': 0,
                         'ignorewhitespace': 1}
                         },
                'old_path': path, 'old_rev': 398,
                'new': 399, 'new_rev': 399, 'new_path': path}
        req = MockRequest(self.env)
        # restricted = False,because we query the whole changeet
        res = cm._render_html(req, self.repos, changeset, False, data)
        for key, val in res.items():
            print(key, repr(val))

        self.assertEqual(9, len(res['changes']))
        self.assertEqual(9, len(set(res['files'])))
        self.assertEqual(u'htgroupsplugin', res['location'])
        # files with changes after processing changeset data in _render_html()
        self.assertEqual(5, res['diff_files'])
        self.assertTrue(res['show_diffs'])
        self.assertFalse(res['has_diffs'])  # No content change, just properties
        # Items which were edited. This is the given file but also the containing parent directories.
        # Filtering is done in render_html()
        self.assertEqual(9, res['filestats']['edit'])
        for file in res['files']:
            self.assertIn(file, (u'htgroupsplugin', u'htgroupsplugin/0.9',
                                 u'htgroupsplugin/0.9/README.txt', u'htgroupsplugin/0.9/TracHtgroups.egg-info',
                                 u'htgroupsplugin/0.9/TracHtgroups.egg-info/trac_plugin.txt',
                                 u'htgroupsplugin/0.9/htgroups', u'htgroupsplugin/0.9/htgroups/__init__.py',
                                 u'htgroupsplugin/0.9/htgroups/htgroups.py',
                                 u'htgroupsplugin/0.9/setup.py'))

    def test_changeset_properties_file_399(self):
        """Check file in a changeset only containing property changes.

        We want to see the change for a file in the changeset. This is special
        because the file only has a property change, same for all the parent directories.
        No content change.

        We call a function in trac.versioncontrol.web_ui.changeset.py which is
        responsible for generating the data for the changeset page.

        NOTE:
        This one may break when someone sets new properties on the whole svn tree
        because this changeset only contains property changes.
        """
        path = 'htgroupsplugin/0.9/README.txt'
        rev = 399
        changeset = SubversionCliChangeset(self.repos, rev)
        self.assertIsInstance(changeset, SubversionCliChangeset)
        changes = list(changeset.get_changes())
        self.assertEqual(9, len(changes))
        cm = ChangesetModule(self.env)

        # Data set in trac.versioncontrol.web_ui.changeset.py -> process_request()
        data = {'repos': self.repos, 'reponame': self.repos.reponame,
                'diff': {'style': u'inline',
                         'options': {'contextall': 1, 'contextlines': 2,
                         'ignorecase': 0,  'ignoreblanklines': 0,
                         'ignorewhitespace': 1}
                         },
                'old_path': path, 'old_rev': 398,
                'new': 399, 'new_rev': 399, 'new_path': path}
        req = MockRequest(self.env)
        # restricted = True,because we query a path
        res = cm._render_html(req, self.repos, changeset, True, data)
        for key, val in res.items():
            print(key, repr(val))

        self.assertEqual(3, len(res['changes']))
        self.assertEqual(3, len(set(res['files'])))
        self.assertEqual(u'htgroupsplugin', res['location'])
        # files with changes after processing changeset data in _render_html()
        self.assertEqual(1, res['diff_files'])
        self.assertTrue(res['show_diffs'])
        self.assertFalse(res['has_diffs'])  # No content change, just properties
        # Items which were edited. This is the given file but also the containing parent directories.
        # Filtering is done in render_html()
        self.assertEqual(3, res['filestats']['edit'])
        for file in res['files']:
            self.assertIn(file, (u'htgroupsplugin', u'htgroupsplugin/0.9', u'htgroupsplugin/0.9/README.txt'))

    def test_timeline_broken_changeset_17976(self):
        """Test get_timeline_events() with interval containing a broken changeset."""
        # Changeset 17976 is empty in 'svn log ...'. Make sure we handle this gracefully.
        repoprovider = DbRepositoryProvider(self.env)
        repoprovider.add_repository(self.repos.reponame, url, type_='svn-cli-direct')
        # There is some broken changeset in this interval: 17976
        start = to_datetime(datetime.datetime(2020, 12, 17, 23, 59, 59, 999999))
        stop = to_datetime(datetime.datetime(2021, 1, 17, 23, 59, 59, 999999))
        cm = ChangesetModule(self.env)
        req = MockRequest(self.env)
        filters = cm.get_timeline_filters(req)[0]
        csets = list(cm.get_timeline_events(req, start, stop, filters))  # This is a generator
        self.assertEqual(17, len(csets))
        for item in csets:
            print(item)


if __name__ == '__main__':
    unittest.main()
