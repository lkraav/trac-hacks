# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
import unittest

from tests import repo_url, sub_repo_url
from trac.test import Mock
from subversioncli.svn_cli import SubversionCliNode, SubversionRepositoryCli


if repo_url.startswith('http'):
    url = '/' + repo_url
else:
    url = '/' + repo_url[6:].lstrip('/')


class TestSvnCliNode(unittest.TestCase):

    @staticmethod
    def _log(msg):
        print(msg)

    def setUp(self):
        self.log = Mock(info=self._log, debug=self._log, error=self._log)
        # self.repos = Mock(repo_url=repo_url, log=self.log)
        parms = {'name': 'Test-Repo', 'id': 1}
        if url.startswith('/http'):
            parms['type'] = 'svn-cli-remote'
        else:
            parms['type'] = 'svn-cli-direct'
        self.repos = SubversionRepositoryCli(url, parms, self.log)

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

    def test_get_file_node_size_0(self):
        """Test getting a file node"""
        # The file has a file size of 0.
        path = 'backlinksmacro/trunk/backlinks/__init__.py'
        rev = 15133
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertEqual(15133, node.created_rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path, node.path)
        self.assertEqual(0, node.size)

    def test_get_file_node_copied(self):
        """Test getting a special file node."""
        # This node is a file in a branch at rev 399. The file wasn't edited after the branching.
        # the file doesn't exist anymore in the tree so it can't be found with
        # ' svn list -r 399 path/in/branch/init.py'
        # The node can't be created, because it's impossible to ge the file size in the branch. (and
        # probably the content, too)
        # See changeset 15264 which triggers the problem
        path = 'htgroupsplugin/trunk/htgroups/__init__.py'
        rev = 399
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertEqual(399, node.created_rev)
        self.assertTrue(node.isfile)
        self.assertFalse(node.isdir)
        self.assertEqual(path, node.path)
        self.assertEqual(72, node.size)

    def test_get_dir_node(self):
        """Test getting a directory node"""
        path = 'customfieldadminplugin/0.11/customfieldadmin'
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
        path = 'customfieldadminplugin/0.11/customfieldadmin'
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

    def test_get_content(self):
        """This file is special because the rev lives in a path which is later copied and
        eventually removed from the tree. This makes finding it in the tree rather difficult.
        node.get_file_size_rev() should have done it though.
        """
        path = 'htgroupsplugin/trunk/htgroups/__init__.py'
        rev = 399
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertEqual(399, node.created_rev)

        with node.get_content() as stream:
            self.assertEqual(72, len(stream.read()))


class TestSvnCliNodeSubtree(unittest.TestCase):
    """Tests for a repo pointing to a subtree."""

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
        # self.repos = Mock(repo_url=repo_url, log=self.log)
        parms = {'name': 'Test-Repo', 'id': 1}
        if self.url.startswith('/http'):
            parms['type'] = 'svn-cli-remote'
        else:
            parms['type'] = 'svn-cli-direct'
        self.repos = SubversionRepositoryCli(self.url, parms, self.log)

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
        self.assertEqual(self.repos.normalize_path(path), node.path)

    def test_get_dir_node(self):
        """Test getting a directory node"""
        path = 'customfieldadminplugin/0.11/customfieldadmin/'
        rev = 11199
        node = SubversionCliNode(self.repos, path, rev, self.log)
        self.assertEqual(rev, node.rev)
        self.assertEqual(11198, node.created_rev)
        self.assertFalse(node.isfile)
        self.assertTrue(node.isdir)
        self.assertEqual(self.repos.normalize_path(path), node.path)

    def test_get_entries(self):
        """Test getting contents of a directory"""
        # We get the directory with rev 11199
        # created_rev is 11198
        path = '0.11/customfieldadmin'
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
        expected = {'0.11/customfieldadmin/__init__.py': {'created_rev': 11198, 'kind': 'file'},
                    '0.11/customfieldadmin/admin.py': {'created_rev': 11198, 'kind': 'file'},
                    '0.11/customfieldadmin/api.py': {'created_rev': 11198, 'kind': 'file'},
                    '0.11/customfieldadmin/htdocs': {'created_rev': 5253, 'kind': 'dir'},
                    '0.11/customfieldadmin/locale': {'created_rev': 11187, 'kind': 'dir'},
                    '0.11/customfieldadmin/templates': {'created_rev': 11187, 'kind': 'dir'},
                    '0.11/customfieldadmin/tests': {'created_rev': 11198, 'kind': 'dir'}
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
