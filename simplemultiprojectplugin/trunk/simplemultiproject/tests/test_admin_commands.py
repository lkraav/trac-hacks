# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
import unittest

from trac.admin.console import TracAdmin
from trac.ticket.model import Ticket
from trac.test import EnvironmentStub
from simplemultiproject.admin_command import SmpAdminCommands
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.tests.util import revert_schema
from simplemultiproject.smp_model import SmpComponent, SmpMilestone, SmpProject, SmpVersion


class TestProjectCommands(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.env.config.set("ticket-custom", "project", "select")
        self.plugin = SmpAdminCommands(self.env)
        # self.env.config.set("ticket-custom", "project", "select")
        self.prj_model = SmpProject(self.env)
        self.comp_model = SmpComponent(self.env)
        self.ms_model = SmpMilestone(self.env)
        self.ver_model = SmpVersion(self.env)

    def tearDown(self):
        self.env.reset_db()

    def _add_projects(self):
        admin = TracAdmin()
        admin.env_set(self.env.path, self.env)
        for prj in (u'Project 1', u'Project 2', u'Project 3'):
            admin.onecmd("project add '%s'" % prj)
        all_prj = self.prj_model.get_all_projects()
        self.assertEqual(3, len(all_prj))
        return admin

    def test_project_add(self):
        admin = TracAdmin()
        admin.env_set(self.env.path, self.env)
        for prj in (u'Project 1', u'Project 2 aöüü', u'Project 3'):
            admin.onecmd("project add '%s'" % prj)
        all_prj = self.prj_model.get_all_projects()
        self.assertEqual(3, len(all_prj))

    def test_project_delete(self):
        admin = self._add_projects()

        admin.onecmd("project remove 'Project 2'")
        all_prj = self.prj_model.get_all_projects()
        self.assertEqual(2, len(all_prj))
        names = [project.name for project in all_prj]
        self.assertNotIn('Project 2', names)
        self.assertIn('Project 1', names)
        self.assertIn('Project 3', names)

    def test_change_summary(self):
        admin = self._add_projects()

        project = self.prj_model.get_project_from_name(u'Project 2')
        self.assertEqual(project.summary, '')
        admin.onecmd("project summary 'Project 2' 'New Summary'")
        project = self.prj_model.get_project_from_name('Project 2')
        self.assertEqual(project.summary, 'New Summary')

    def test_change_description(self):
        admin = self._add_projects()

        project = self.prj_model.get_project_from_name(u'Project 2')
        self.assertEqual(project.description, '')
        admin.onecmd("project describe 'Project 2' 'New Description'")
        project = self.prj_model.get_project_from_name('Project 2')
        self.assertEqual(project.description, 'New Description')

    def test_change_restriction(self):
        admin = self._add_projects()

        project = self.prj_model.get_project_from_name(u'Project 2')
        self.assertEqual(project.restricted, '')
        admin.onecmd("project restrict 'Project 2' Yes")
        project = self.prj_model.get_project_from_name('Project 2')
        self.assertEqual(project.restricted, 'YES')

        admin.onecmd("project restrict 'Project 2' nope")  # Invalid parameter 'nope'
        project = self.prj_model.get_project_from_name('Project 2')
        self.assertEqual(project.restricted, 'YES')

        admin.onecmd("project restrict 'Project 2' no")
        project = self.prj_model.get_project_from_name('Project 2')
        self.assertEqual(project.restricted, '')

    def test_rename_project(self):
        # Preparation
        admin = self._add_projects()
        projects = self.prj_model.get_all_projects()
        for data in projects:
            tkt = Ticket(self.env)
            tkt['summary'] = data.summary
            tkt['project'] = data.name
            tkt.insert()

        # Check data
        project = self.prj_model.get_project_from_name(u'Project 2')
        self.assertIsNotNone(project)
        project_id = project.id  # Use later to find the project after renaming
        # key: ticket id, val: project name
        tcustom = {data[0]: data[2] for data in self.env.db_query("SELECT * FROM ticket_custom "
                                                                  "WHERE name = 'project'")}
        for tkt_id in range(3):
            tkt = Ticket(self.env, tkt_id + 1)
            self.assertIsNotNone(tkt)
            self.assertEqual(tkt['project'], tcustom[tkt_id + 1])  # ticket custom data is same as ticket data

        # Test starts here
        admin.onecmd("project rename 'Project 2' 'New Name'")
        projects = self.prj_model.get_all_projects()
        # project data
        for prj in projects:
            if prj.id == project_id:
                self.assertEqual(prj.name, 'New Name')
        # Ticket custom data
        # key: ticket id, val: project name
        tcustom = {data[0]: data[2] for data in self.env.db_query("SELECT * FROM ticket_custom "
                                                                  "WHERE name = 'project'")}
        self.assertEqual('New Name', tcustom[2])  # ticket custom data must reflect new name

    def test_open_project(self):
        admin = self._add_projects()
        project = self.prj_model.get_project_from_name(u'Project 2')
        self.prj_model.update(project.id, project.name, project.summary, project.description,
                                    12340000, project.restricted)

        project = self.prj_model.get_project_from_name(u'Project 2')
        self.assertEqual(project.closed, 12340000)
        admin.onecmd("project open 'Project 2'")
        project = self.prj_model.get_project_from_name('Project 2')
        self.assertIsNone(project.closed)

    def test_close_project(self):
        admin = self._add_projects()
        project = self.prj_model.get_project_from_name(u'Project 2')
        self.assertIsNone(project.closed)
        admin.onecmd("project close 'Project 2'")
        project = self.prj_model.get_project_from_name('Project 2')
        self.assertIsNotNone(project.closed)

    def test_assign_project_component(self):
        admin = self._add_projects()
        self.assertListEqual([], self.comp_model.get_all_components_and_project_id())
        projects = self.prj_model.get_all_projects()
        self.assertEqual(3, len(projects))

        for project in projects:
            admin.onecmd("project assign component '%s' '%s'" % (project.name, project.name + 'item'))

        comps = self.comp_model.get_all_components_and_project_id()
        self.assertEqual(3, len(comps))
        pdict = {project.id: project.name for project in projects}
        for comp in comps:
            self.assertEqual(comp[0], pdict[comp[1]] + 'item')

    def test_assign_project_milestone(self):
        admin = self._add_projects()
        self.assertListEqual([], self.ms_model.get_all_milestones_and_id_project_id())
        projects = self.prj_model.get_all_projects()
        self.assertEqual(3, len(projects))

        for project in projects:
            admin.onecmd("project assign milestone '%s' '%s'" % (project.name, project.name + 'item'))

        items = self.ms_model.get_all_milestones_and_id_project_id()
        self.assertEqual(3, len(items))
        pdict = {project.id: project.name for project in projects}
        for comp in items:
            self.assertEqual(comp[0], pdict[comp[1]] + 'item')

    def test_assign_project_version(self):
        admin = self._add_projects()
        self.assertListEqual([], self.ver_model.get_all_versions_and_project_id())
        projects = self.prj_model.get_all_projects()
        self.assertEqual(3, len(projects))

        for project in projects:
            admin.onecmd("project assign version '%s' '%s'" % (project.name, project.name + 'item'))

        items = self.ver_model.get_all_versions_and_project_id()
        self.assertEqual(3, len(items))
        pdict = {project.id: project.name for project in projects}
        for comp in items:
            self.assertEqual(comp[0], pdict[comp[1]] + 'item')

    def test_unassign_project_component(self):
        admin = self._add_projects()
        self.assertListEqual([], self.comp_model.get_all_components_and_project_id())
        projects = self.prj_model.get_all_projects()
        pdict = {project.id: project.name for project in projects}
        self.assertEqual(3, len(projects))

        for project in projects:
            admin.onecmd("project assign component '%s' '%s'" % (project.name, project.name + 'item'))
        items = self.comp_model.get_all_components_and_project_id()
        self.assertEqual(3, len(items))

        # Test starts here
        admin.onecmd("project unassign component '%s'" % 'Project 2item')
        items = self.comp_model.get_all_components_and_project_id()
        self.assertEqual(2, len(items))

        names = []
        for comp in items:
            self.assertEqual(comp[0], pdict[comp[1]] + 'item')
            names.append(pdict[comp[1]] + 'item')
        self.assertNotIn('Project 2item', names)  # Make sure we removed the right one...

        # Test component removal when assigned to two projects: 'Project 1' and 'Project 3'
        # Note that another component 'Project 1item' is assigned to 'Project 1'
        admin.onecmd("project assign component '%s' '%s'" % ('Project 1', 'Project 3item'))
        items = self.comp_model.get_all_components_and_project_id()
        self.assertEqual(3, len(items))

        admin.onecmd("project unassign component '%s'" % 'Project 3item')
        items = self.comp_model.get_all_components_and_project_id()
        self.assertEqual(1, len(items))
        self.assertEqual('Project 1item', items[0][0])

    def test_unassign_project_milestone(self):
        admin = self._add_projects()
        self.assertListEqual([], self.ms_model.get_all_milestones_and_id_project_id())
        projects = self.prj_model.get_all_projects()
        pdict = {project.id: project.name for project in projects}
        self.assertEqual(3, len(projects))

        for project in projects:
            admin.onecmd("project assign milestone '%s' '%s'" % (project.name, project.name + 'item'))
        items = self.ms_model.get_all_milestones_and_id_project_id()
        self.assertEqual(3, len(items))

        # Test starts here
        admin.onecmd("project unassign milestone '%s'" % 'Project 2item')
        items = self.ms_model.get_all_milestones_and_id_project_id()
        self.assertEqual(2, len(items))

        names = []
        for comp in items:
            self.assertEqual(comp[0], pdict[comp[1]] + 'item')
            names.append(pdict[comp[1]] + 'item')
        self.assertNotIn('Project 2item', names)  # Make sure we removed the right one...

        # Test milestone removal when assigned to two projects: 'Project 1' and 'Project 3'
        # Note that another milestone 'Project 1item' is assigned to 'Project 1'
        admin.onecmd("project assign milestone '%s' '%s'" % ('Project 1', 'Project 3item'))
        items = self.ms_model.get_all_milestones_and_id_project_id()
        self.assertEqual(3, len(items))

        admin.onecmd("project unassign milestone '%s'" % 'Project 3item')
        items = self.ms_model.get_all_milestones_and_id_project_id()
        self.assertEqual(1, len(items))
        self.assertEqual('Project 1item', items[0][0])

    def test_unassign_project_version(self):
        admin = self._add_projects()
        self.assertListEqual([], self.ver_model.get_all_versions_and_project_id())
        projects = self.prj_model.get_all_projects()
        pdict = {project.id: project.name for project in projects}
        self.assertEqual(3, len(projects))

        for project in projects:
            admin.onecmd("project assign version '%s' '%s'" % (project.name, project.name + 'item'))
        items = self.ver_model.get_all_versions_and_project_id()
        self.assertEqual(3, len(items))

        # Test starts here
        admin.onecmd("project unassign version '%s'" % 'Project 2item')
        items = self.ver_model.get_all_versions_and_project_id()
        self.assertEqual(2, len(items))

        names = []
        for comp in items:
            self.assertEqual(comp[0], pdict[comp[1]] + 'item')
            names.append(pdict[comp[1]] + 'item')
        self.assertNotIn('Project 2item', names)  # Make sure we removed the right one...

        # Test version removal when assigned to two projects: 'Project 1' and 'Project 3'
        # Note that another version 'Project 1item' is assigned to 'Project 1'
        admin.onecmd("project assign version '%s' '%s'" % ('Project 1', 'Project 3item'))
        items = self.ver_model.get_all_versions_and_project_id()
        self.assertEqual(3, len(items))

        admin.onecmd("project unassign version '%s'" % 'Project 3item')
        items = self.ver_model.get_all_versions_and_project_id()
        self.assertEqual(1, len(items))
        self.assertEqual('Project 1item', items[0][0])

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
