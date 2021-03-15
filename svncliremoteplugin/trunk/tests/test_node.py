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
from subversioncli.svn_cli import SubversionCliNode


class TestSvnCliNode(unittest.TestCase):

    @staticmethod
    def _log(msg):
        print(msg)

    def setUp(self):
        self.log = Mock(info=self._log)
        self.repos = Mock(repo_url=repo_url, log=self.log)

    def test_get_file_node(self):
        """Test getting a file node"""
        # The file was created with 2250, copied in 11177 and again 2388
        # and modified in between up to 11187. Next change was in 11198
        path = 'customfieldadminplugin/0.11/customfieldadmin/admin.py'
        rev = 11190
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertEqual(11187, node.created_rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path, node.path)

    def test_get_dir_node(self):
        """Test getting a directory node"""
        path = 'customfieldadminplugin/0.11/customfieldadmin/'
        rev = 11199
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertEqual(11198, node.created_rev)
        self.assertFalse(node.isfile)
        self.assertTrue(node.isdir)
        self.assertEqual(path, node.path)

    def test_get_entries(self):
        """Test getting contents of a directory"""
        # We get the directory with rev 11199
        # created_rev is 11198
        path = 'customfieldadminplugin/0.11/customfieldadmin/'
        rev = 11199  # That's the subversion tree revision
        node = SubversionCliNode(self.repos, path, rev, self.log)
        # Check if directory node is properly initialized
        self.assertEqual(rev, node.rev)
        self.assertEqual(11198, node.created_rev)  # created revision is different from tree
        self.assertFalse(node.isfile)
        self.assertTrue(node.isdir)
        self.assertEqual(path, node.path)
        #
        # Check the method
        #
        expected = {'customfieldadminplugin/0.11/customfieldadmin/__init__.py': {'created_rev': 11198, 'kind': 'file'},
                    'customfieldadminplugin/0.11/customfieldadmin/admin.py': {'created_rev': 11198, 'kind': 'file'},
                    'customfieldadminplugin/0.11/customfieldadmin/api.py': {'created_rev': 11198, 'kind': 'file'},
                    'customfieldadminplugin/0.11/customfieldadmin/htdocs': {'created_rev': 5253, 'kind': 'dir'},
                    'customfieldadminplugin/0.11/customfieldadmin/locale': {'created_rev': 11187, 'kind': 'dir'},
                    'customfieldadminplugin/0.11/customfieldadmin/templates': {'created_rev': 11187, 'kind': 'dir'},
                    'customfieldadminplugin/0.11/customfieldadmin/tests': {'created_rev': 11198, 'kind': 'dir'}
                    }
        entries = list(node.get_entries())
        self.assertEqual(7, len(entries))
        for entry in entries:
            self.assertIsInstance(entry, SubversionCliNode)
            attrs = expected[entry.path]
            self.assertEqual(attrs['created_rev'], entry.created_rev)
            self.assertEqual(attrs['kind'], entry.kind)


if __name__ == '__main__':
    unittest.main()
