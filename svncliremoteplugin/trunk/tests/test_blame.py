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
from subversioncli.svn_cli import SubversionRepositoryCli
from subversioncli.svn_client import get_blame_annotations


class TestBlameAnnotations(unittest.TestCase):
    """Test function get_blame_annotations()"""

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

    def test_blame_2389(self):
        """Test blame annotations for a file with svn-copy."""
        # The file was created with 2250, copied 2388, and modified in 2389
        expected = [2250, 2250, 2250,
                    2389,
                    2250, 2250,
                    2389,
                    2250, 2250, 2250,
                    2389, 2389, 2389, 2389]
        path = 'customfieldadminplugin/0.11/setup.py'
        blame = get_blame_annotations(self.repos, 2389, path)
        self.assertEqual(14, len(blame))
        for idx, rev in enumerate(blame):
            self.assertEqual(expected[idx], rev)

    def test_blame_11187(self):
        """Test blame annotations for a file with svn-copy."""
        # The file was created with 2250, copied in 11177 and 2388, and modified in between up to 11187
        expected = [2250, 2250, 2250, 2250, 2250, 2250,
                    11168, 5236,
                    2250, 2250,
                    6485, 2250,
                    11187, 11187,
                    2389, 2250, 11177, 2250, 11177, 2250
                   ]
        path = 'customfieldadminplugin/0.11/customfieldadmin/admin.py'
        blame = get_blame_annotations(self.repos, 11187, path)
        self.assertEqual(136, len(blame))
        for idx, rev in enumerate(blame[:20]):
            self.assertEqual(expected[idx], rev)


class TestBlameAnnotationsSubtree(unittest.TestCase):
    """Test function get_blame_annotations()"""

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

    def test_blame_2389(self):
        """Test blame annotations for a file with svn-copy."""
        # The file was created with 2250, copied 2388, and modified in 2389
        expected = [2250, 2250, 2250,
                    2389,
                    2250, 2250,
                    2389,
                    2250, 2250, 2250,
                    2389, 2389, 2389, 2389]
        path = 'customfieldadminplugin/0.11/setup.py'
        # The path is normalized in the node. So we do it here, too.
        blame = get_blame_annotations(self.repos, 2389, self.repos.normalize_path(path))
        self.assertEqual(14, len(blame))
        for idx, rev in enumerate(blame):
            self.assertEqual(expected[idx], rev)

    def test_blame_11187(self):
        """Test blame annotations for a file with svn-copy."""
        # The file was created with 2250, copied in 11177 and 2388, and modified in between up to 11187
        expected = [2250, 2250, 2250, 2250, 2250, 2250,
                    11168, 5236,
                    2250, 2250,
                    6485, 2250,
                    11187, 11187,
                    2389, 2250, 11177, 2250, 11177, 2250
                   ]
        path = '0.11/customfieldadmin/admin.py'
        blame = get_blame_annotations(self.repos, 11187, path)
        self.assertEqual(136, len(blame))
        for idx, rev in enumerate(blame[:20]):
            self.assertEqual(expected[idx], rev)


if __name__ == '__main__':
    unittest.main()
