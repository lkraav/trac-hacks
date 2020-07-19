# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.test import EnvironmentStub
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.smp_model import SmpProject
from simplemultiproject.permission import SmpPermission
from simplemultiproject.tests.util import revert_schema


class TestPermisssionProvider(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prj_model = SmpProject(self.env)
        self.perm_plugin = SmpPermission(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_permission_no_projects(self):
        """This should be [PROJECT_SETTINGS_VIEW, (PROJECTS_ADMIN, [PROJECT_STTINGS_VIEW])]"""
        perms = self.perm_plugin.get_permission_actions()
        self.assertEqual(2, len(perms))
        for item in perms:
            if isinstance(item, tuple):
                self.assertEqual(2, len(item))
                self.assertEqual('PROJECT_ADMIN', item[0])
                self.assertEqual('PROJECT_SETTINGS_VIEW', item[1][0])
            else:
                self.assertEqual('PROJECT_SETTINGS_VIEW', item)

    def test_permission_projects(self):
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name)
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        # Permission check starts here
        expected = ['PROJECT_1_MEMBER',
                    'PROJECT_2_MEMBER',
                    'PROJECT_3_MEMBER',
                    'PROJECT_4_MEMBER',
                    'PROJECT_SETTINGS_VIEW']

        perms = self.perm_plugin.get_permission_actions()
        self.assertEqual(6, len(perms))  # 2 * admin perms + 4 * project member perms
        for item in perms:
            if isinstance(item, tuple):
                # PROJECT_ADMIN is a meta permission
                self.assertEqual(2, len(item))
                self.assertEqual('PROJECT_ADMIN', item[0])
                self.assertEqual(5, len(item[1]))  # PROJECT_STTINGS_VIEW + 4 * project member
                perm_lst = sorted(item[1])
                self.assertSequenceEqual(perm_lst, expected)
            else:
                # project member perms and PROJECT_STTINGS_VIEW are strings
                self.assertIn(item, expected)  # this doesn't check for distinctiveness

        # Check only the non tuple perms
        perm_lst = [item for item in perms if not isinstance(item, tuple)]
        perm_lst.sort()
        self.assertEqual(5, len(perm_lst))
        self.assertSequenceEqual(perm_lst, expected)  # This will check for duplicates

    def test_permission_projects_delete_prj(self):
        # We first create some projects. Then one project is removed. The new list of project member perms
        # must be visible
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name)
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        self.prj_model.delete(2)

        # Permission check starts here
        expected = ['PROJECT_1_MEMBER',
                    'PROJECT_3_MEMBER',
                    'PROJECT_4_MEMBER',
                    'PROJECT_SETTINGS_VIEW']

        perms = self.perm_plugin.get_permission_actions()
        self.assertEqual(5, len(perms))  # 2 * admin perms + 3 * project member perms
        for item in perms:
            if isinstance(item, tuple):
                # PROJECT_ADMIN is a meta permission
                self.assertEqual(2, len(item))
                self.assertEqual('PROJECT_ADMIN', item[0])
                self.assertEqual(4, len(item[1]))  # PROJECT_STTINGS_VIEW + 3 * project member
                perm_lst = sorted(item[1])
                self.assertSequenceEqual(perm_lst, expected)
            else:
                # project member perms and PROJECT_STTINGS_VIEW are strings
                self.assertIn(item, expected)  # this doesn't check for distinctiveness

        # Check only the non tuple perms
        perm_lst = [item for item in perms if not isinstance(item, tuple)]
        perm_lst.sort()
        self.assertEqual(4, len(perm_lst))
        self.assertSequenceEqual(perm_lst, expected)  # This will check for duplicates

    def test_permission_projects_delete_add_prj(self):
        # We first create some projects. Then one project is removed and added again. The project must have a new
        # id .The new list of project member perms must be returnd by the plugin
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name)
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        self.prj_model.delete(2)
        p_id = self.prj_model.add('p 2')  # This one should get a new id.
        self.assertEqual(5, p_id)

        # Permission check starts here
        expected = ['PROJECT_1_MEMBER',
                    'PROJECT_3_MEMBER',
                    'PROJECT_4_MEMBER',
                    'PROJECT_5_MEMBER',
                    'PROJECT_SETTINGS_VIEW']

        perms = self.perm_plugin.get_permission_actions()
        self.assertEqual(6, len(perms))  # 2 * admin perms + 4 * project member perms
        for item in perms:
            if isinstance(item, tuple):
                # PROJECT_ADMIN is a meta permission
                self.assertEqual(2, len(item))
                self.assertEqual('PROJECT_ADMIN', item[0])
                self.assertEqual(5, len(item[1]))  # PROJECT_STTINGS_VIEW + 4 * project member
                perm_lst = sorted(item[1])
                self.assertSequenceEqual(perm_lst, expected)
            else:
                # project member perms and PROJECT_STTINGS_VIEW are strings
                self.assertIn(item, expected)  # this doesn't check for distinctiveness

        # Check only the non tuple perms
        perm_lst = [item for item in perms if not isinstance(item, tuple)]
        perm_lst.sort()
        self.assertEqual(5, len(perm_lst))
        self.assertSequenceEqual(perm_lst, expected)  # This will check for duplicates


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPermisssionProvider))

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
