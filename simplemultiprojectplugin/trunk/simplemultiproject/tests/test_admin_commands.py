# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.admin.console import TracAdmin
from trac.test import EnvironmentStub
from simplemultiproject.admin_command import SmpAdminCommands
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.tests.util import revert_schema
from simplemultiproject.smp_model import SmpComponent, SmpProject, SmpVersion


class TestProjectCommands(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpAdminCommands(self.env)
        # self.env.config.set("ticket-custom", "project", "select")
        self.prj_model = SmpProject(self.env)
        self.comp_model = SmpComponent(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_project_add(self):
        admin = TracAdmin()
        admin.env_set(self.env.path, self.env)
        for prj in (u'Project 1', u'Project 2', u'Project 3'):
            admin.onecmd("project add '%s'" % prj)
        all_prj = self.prj_model.get_all_projects()
        self.assertEqual(3, len(all_prj))


class TestComponentCommands(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpAdminCommands(self.env)
        # self.env.config.set("ticket-custom", "project", "select")
        self.prj_model = SmpProject(self.env)
        self.comp_model = SmpComponent(self.env)
        self.admin = TracAdmin()
        self.admin.env_set(self.env.path, self.env)
        for prj in (u'Project 1', u'Project 2', u'Project 3'):
            self.admin.onecmd("project add '%s'" % prj)

    def tearDown(self):
        self.env.reset_db()

    def test_component(self):
        admin = self.admin
        all_prj = self.prj_model.get_all_projects()
        self.assertEqual(3, len(all_prj))

        for comp in (u'Comp 1', u'Comp 2', u'Comp 3'):
            admin.onecmd("project assign component 'Project 1' '%s'" % comp)
            admin.onecmd("project assign component 'Project 2' '%s'" % comp)
            admin.onecmd("project assign component 'Project 3' '%s'" % comp)

        for p_id in (1, 2, 3):
            res = self.comp_model.get_components_for_project_id(p_id)
            self.assertIn(u'Comp 1', res)

        admin.onecmd("project unassign component 'Comp 1'")  # This renoves the component from all projects
        for p_id in (1, 2, 3):
            res = self.comp_model.get_components_for_project_id(p_id)
            self.assertNotIn(u'Comp 1', res)

        for p_id in (1, 2, 3):
            res = self.comp_model.get_components_for_project_id(p_id)
            self.assertIn(u'Comp 2', res)  # Make sure only one component was removed before


class TestVersionCommands(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.plugin = SmpAdminCommands(self.env)
        # self.env.config.set("ticket-custom", "project", "select")
        self.prj_model = SmpProject(self.env)
        self.comp_model = SmpVersion(self.env)
        self.admin = TracAdmin()
        self.admin.env_set(self.env.path, self.env)
        for prj in (u'Project 1', u'Project 2', u'Project 3'):
            self.admin.onecmd("project add '%s'" % prj)

    def tearDown(self):
        self.env.reset_db()

    def test_version(self):
        admin = self.admin
        all_prj = self.prj_model.get_all_projects()
        self.assertEqual(3, len(all_prj))

        for item in (u'Ver 1', u'Ver 2', u'Ver 3'):
            admin.onecmd("project assign version 'Project 1' '%s'" % item)
            admin.onecmd("project assign version 'Project 2' '%s'" % item)
            admin.onecmd("project assign version 'Project 3' '%s'" % item)

        for p_id in (1, 2, 3):
            res = self.comp_model.get_versions_for_project_id(p_id)
            self.assertIn(u'Ver 1', res)

        admin.onecmd("project unassign version 'Ver 1'")  # This renoves the version from all projects
        for p_id in (1, 2, 3):
            res = self.comp_model.get_versions_for_project_id(p_id)
            self.assertNotIn(u'Ver 1', res)

        for p_id in (1, 2, 3):
            res = self.comp_model.get_versions_for_project_id(p_id)
            self.assertIn(u'Ver 2', res)  # Make sure only one version was removed before


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestComponentCommands))
    suite.addTest(unittest.makeSuite(TestProjectCommands))
    suite.addTest(unittest.makeSuite(TestVersionCommands))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
