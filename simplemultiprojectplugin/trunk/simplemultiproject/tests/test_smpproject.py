# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
import unittest
from collections import defaultdict
from pkg_resources import get_distribution, parse_version
from trac.admin.console import TracAdmin
from trac.perm import PermissionSystem
from trac.test import EnvironmentStub
from trac.ticket.model import Ticket
from simplemultiproject.environmentSetup import smpEnvironmentSetupParticipant
from simplemultiproject.smp_model import PERM_TEMPLATE, SmpComponent, SmpMilestone, SmpProject, SmpVersion
from simplemultiproject.tests.util import revert_schema


# For python 3. Note that basestring is only used for testing, but not in the
# codenase
try:
  basestring
except NameError:
  basestring = str


class TestSmpProjectAdd(unittest.TestCase):
    """Test add() method of class SmpPorject"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prj_model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_project_add_name_only(self):
        """Test add() of SmpProject with project name only"""
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name)
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

    def test_project_add_summary_desc(self):
        """Test add() of SmpProject with project name, summary and description"""
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name, summary=name + u'summary äöü', description=name + u'desc äöü')
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        for item in self.prj_model.get_all_projects():
            self.assertEqual(item[1] + u'summary äöü', item[2])
            self.assertEqual(item[1] + u'desc äöü', item[3])
            prj_id = int(item[1].split()[1])  # derived from name. This works because of auto increment
            self.assertEqual(item[0], prj_id)


class TestSmpProjectDelete(unittest.TestCase):
    """Test add() method of class SmpPorject"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prjmodel = SmpProject(self.env)
        self.msmodel = SmpMilestone(self.env)
        self.vermodel = SmpVersion(self.env)
        self.compmodel = SmpComponent(self.env)

        self.projects = (("Name: Prj 1", 'Summary 1', 'Foo Bar', None, "YES"),
                         ("Name: Prj 2", 'Summary 2', 'Description 2', None, None),
                         ("Name: Prj 3", 'Summary 3', 'Description 3', None, ""),
                         ("Name: Prj 4", 'Summary 4', 'Baz Foo', None, "YES"),
                         ("Name: Prj 5", 'Summary 5', 'Description 5', None, None),
                         ("Name: Prj 6", 'Summary 6', 'Baz Foo Bar', None, "YES"),
                         )

        for item in self.projects:
            self.prjmodel.add(*item)

        self.milestones = (("ms 1", 2), ("ms 2", 1), ("ms 3", 2))
        for item in self.milestones:
            self.msmodel.add(*item)

        self.components = (("comp 1", 1), ("comp 2", 3), ("comp 3", 2))
        for item in self.components:
            self.compmodel.add(*item)

        self.versions = (("ver 1", 3), ("ver 2",  2), ("ver 3", 1))
        for item in self.versions:
            self.vermodel.add(*item)

    def tearDown(self):
        self.env.reset_db()

    def check_test_setup(self):
        # Check test setup first
        self.assertEqual(1, len(self.compmodel.get_components_for_project_id(1)))
        self.assertEqual(1, len(self.compmodel.get_components_for_project_id(2)))
        self.assertEqual(1, len(self.compmodel.get_components_for_project_id(3)))

        self.assertEqual(1, len(self.msmodel.get_milestones_for_project_id(1)))
        self.assertEqual(2, len(self.msmodel.get_milestones_for_project_id(2)))

        self.assertEqual(1, len(self.vermodel.get_versions_for_project_id(1)))
        self.assertEqual(1, len(self.vermodel.get_versions_for_project_id(2)))
        self.assertEqual(1, len(self.vermodel.get_versions_for_project_id(3)))

        self.assertEqual(6, len(self.prjmodel.get_all_projects()))

    def test_delete_single_project_from_db(self):
        self.check_test_setup()
        self.prjmodel.delete(2)  # this one has two milestones associated

        comps = self.compmodel.get_all_components_and_project_id()
        self.assertEqual(2, len(comps))
        for comp in comps:
            self.assertIn(comp[0], ("comp 1", "comp 2"))

        milestones = self.msmodel.get_all_milestones_and_id_project_id()
        self.assertEqual(1, len(milestones))
        self.assertEqual(milestones[0][0], "ms 2")

        versions = self.vermodel.get_all_versions_and_project_id()
        self.assertEqual(2, len(versions))
        for ver in versions:
            self.assertIn(ver[0], ("ver 1", "ver 3"))

    def test_delete_multiple_projects_from_db(self):
        self.check_test_setup()
        self.prjmodel.delete([3, 2])  # this one has two milestones associated

        comps = self.compmodel.get_all_components_and_project_id()
        self.assertEqual(1, len(comps))
        for comp in comps:
            self.assertEqual(comp[0], "comp 1")

        milestones = self.msmodel.get_all_milestones_and_id_project_id()
        self.assertEqual(1, len(milestones))
        self.assertEqual(milestones[0][0], "ms 2")

        versions = self.vermodel.get_all_versions_and_project_id()
        self.assertEqual(1, len(versions))
        for ver in versions:
            self.assertEqual(ver[0], "ver 3")

    def _prepare_permissions(self):
        def _get_known_users(cnx=None):
            """Taken from Trac 1.2.x """
            return self.env.db_query("""
                    SELECT DISTINCT s.sid, n.value, e.value
                    FROM session AS s
                     LEFT JOIN session_attribute AS n ON (n.sid=s.sid
                      AND n.authenticated=1 AND n.name = 'name')
                     LEFT JOIN session_attribute AS e ON (e.sid=s.sid
                      AND e.authenticated=1 AND e.name = 'email')
                    WHERE s.authenticated=1 ORDER BY s.sid
            """)

        permsys = PermissionSystem(self.env)
        projects = self.prjmodel.get_all_projects()

        # Permission provider must give us a permission for each project
        perms = permsys.get_user_permissions()
        for pr_id in range(5):
            self.assertIn(PERM_TEMPLATE % (pr_id + 1), perms)

        for pr_id in (7, 8):
            self.assertNotIn(PERM_TEMPLATE % pr_id, perms)

        # Grant user permissions
        for project in projects:
            if project.restricted:
                users = project.description.split()
                for user in users:
                    permsys.grant_permission(user, PERM_TEMPLATE % project.id)

        # Just check if we granted the right permissions
        for project in projects:
            if project.restricted:
                for user in project.description.split():
                    perms = permsys.get_user_permissions(user)
                    self.assertTrue(PERM_TEMPLATE % project.id in perms and perms[PERM_TEMPLATE % project.id])
                    self.assertTrue(PERM_TEMPLATE % 2 not in perms or not perms[PERM_TEMPLATE % 2])

        # Make users known to Trac otherwise we can't query the user list for a permission
        admin = TracAdmin()
        admin.env_set(self.env.path, self.env)
        for user in (u'Foo', u'Bar', u'Baz', u'FooBar', u"FooBaz"):
            admin.onecmd("session add %s" % user)

        if parse_version(get_distribution("Trac").version) < parse_version('1.1'):
            # See #13923
            # With Trac 1.2 stub method get_know_users() is gone from EnvironmentStub. This method returned
            # the empty (default) instance variable 'known_users'. This test code uses somewhere deep down the
            # user information thus failing when not finding any users. With Trac 1.2 the users are queried by the
            # real Environment object from the database.
            # Here the known users are added for Trac 1.0.
            self.env.known_users = list(_get_known_users())

    def test_delete_multiple_projects_permissions(self):
        """Test if permission are removed from system and user after deletion of projects.

        When projects are deleted any permissions granted to users are deleted from the user.
        """
        self.check_test_setup()
        self._prepare_permissions()

        self.prjmodel.delete([1, 4])  # this one has two milestones associated

        # Permission provider must give us a permission for each project
        permsys = PermissionSystem(self.env)
        perms = permsys.get_user_permissions()
        for pr_id in (1, 4):
            self.assertNotIn(PERM_TEMPLATE % pr_id, perms)

        for pr_id in (2, 3, 5, 6):
            self.assertIn(PERM_TEMPLATE % pr_id, perms)

        # Test user permissions
        perms = permsys.get_user_permissions('Foo')
        for pr_id in (1, 4, 2, 3, 5):  # unrestricted projects don't have permission set either
            self.assertNotIn(PERM_TEMPLATE % pr_id, perms)
        for pr_id in (6,):  # unrestricted projects ae not included here
            self.assertIn(PERM_TEMPLATE % pr_id, perms)

        perms = permsys.get_user_permissions('Bar')
        for pr_id in (1, 2, 3, 4, 5):  # unrestricted projects don't have permission set either
            self.assertNotIn(PERM_TEMPLATE % pr_id, perms)
        for pr_id in (6,):  # unrestricted projects ae not included here
            self.assertIn(PERM_TEMPLATE % pr_id, perms)

        perms = permsys.get_user_permissions('Baz')
        for pr_id in (1, 2, 3, 4, 5):  # unrestricted projects don't have permission set either
            self.assertNotIn(PERM_TEMPLATE % pr_id, perms)
        for pr_id in (6,):  # unrestricted projects ae not included here
            self.assertIn(PERM_TEMPLATE % pr_id, perms)

        perms = permsys.get_user_permissions('FooBaz')
        for pr_id in (1, 2, 3, 4, 5, 6):
            self.assertNotIn(PERM_TEMPLATE % pr_id, perms)


class TestSmpProjectExists(unittest.TestCase):
    """Test project_exists() method of SmpProject"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prj_model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_project_exist_no_prj(self):
        self.assertFalse(self.prj_model.project_exists())
        self.assertFalse(self.prj_model.project_exists(project_id=1))
        self.assertFalse(self.prj_model.project_exists(project_name='foo'))

    def test_project_exist(self):
        # prepare data
        prjs = ((1, 'p 1'), (2, 'p 2'), (3, 'p 3'), (4, 'p 4'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name, summary=name + u'summary äöü', description=name + u'desc äöü')
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        # Check inserted projects
        for p_id, name in prjs:
            self.assertTrue(self.prj_model.project_exists(project_id=p_id))
            self.assertTrue(self.prj_model.project_exists(project_name=name))

        # negative test
        self.assertFalse(self.prj_model.project_exists(project_id=5))
        self.assertFalse(self.prj_model.project_exists(project_name='foo'))

        # Test deleted projects


class TestSmpProjectGetAllProjects(unittest.TestCase):
    """Test get_all_projects() method of SmpProject"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prj_model = SmpProject(self.env)

    def tearDown(self):
        self.env.reset_db()

    def test_get_all_projects(self):
        """Test method get_all_projects of SmpProject"""
        prjs = ((1, 'zz 1'), (2, 'bb 2'), (3, 'p 3'), (4, 'aa 4'), (5, 'gg 2'), (6, 'a 2'), (7, 'z 2'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name, summary=name + u'summary äöü', description=name + u'desc äöü',
                                        closed=100, restrict_to='YES')
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        projects = self.prj_model.get_all_projects()
        prj = projects[0]
        self.assertEqual(7, len(projects))
        self.assertEqual(6, len(prj))  # check length of returned tuple
        # Check types
        self.assertIsInstance(prj.id, int)
        self.assertIsInstance(prj.name, basestring)
        self.assertIsInstance(prj.summary, basestring)
        self.assertIsInstance(prj.description, basestring)
        self.assertIsInstance(prj.closed, int)
        self.assertIsInstance(prj.restricted, basestring)

    def test_get_all_projects_is_sorted(self):
        """Test if method get_all_projects() returns a list sorted by name"""
        prjs = ((1, 'zz 1'), (2, 'bb 2'), (3, 'p 3'), (4, 'aa 4'), (5, 'gg 2'), (6, 'a 2'), (7, 'z 2'))
        for p_id, name in prjs:
            prj_id = self.prj_model.add(name, summary=name + u'summary äöü', description=name + u'desc äöü',
                                        closed=100, restrict_to='YES')
            self.assertEqual(p_id, prj_id)  # prj_id is auto increment

        prjs_complete = [(prj[0], prj[1], prj[1] + u'summary äöü', prj[1] + u'desc äöü', 100, 'YES') for prj in prjs]
        projects = self.prj_model.get_all_projects()
        self.assertNotEqual(prjs_complete[0][1], projects[0].name)
        prjs_complete.sort(key=lambda prj: prj[1])
        self.assertListEqual(prjs_complete, projects)


class TestSmpProjectApplyRestrictions(unittest.TestCase):
    """Test project filtering by permission and user"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prjmodel = SmpProject(self.env)
        self.msmodel = SmpMilestone(self.env)
        self.vermodel = SmpVersion(self.env)
        self.compmodel = SmpComponent(self.env)

        self.projects = (("Name: Prj 1", 'Summary 1', 'Foo Bar', None, "YES"),
                         ("Name: Prj 2", 'Summary 2', 'Description 2', None, None),
                         ("Name: Prj 3", 'Summary 3', 'Description 3', None, ""),
                         ("Name: Prj 4", 'Summary 4', 'Baz Foo', None, "YES"),
                         ("Name: Prj 5", 'Summary 5', 'Description 5', None, None),
                         ("Name: Prj 6", 'Summary 6', 'Baz Foo Bar', None, "YES"),
                         )

        for item in self.projects:
            self.prjmodel.add(*item)

        self.milestones = (("ms 1", 2), ("ms 2", 1), ("ms 3", 2))
        for item in self.milestones:
            self.msmodel.add(*item)

        self.components = (("comp 1", 1), ("comp 2", 3), ("comp 3", 2))
        for item in self.components:
            self.compmodel.add(*item)

        self.versions = (("ver 1", 3), ("ver 2",  2), ("ver 3", 1))
        for item in self.versions:
            self.vermodel.add(*item)

    def tearDown(self):
        self.env.reset_db()

    def test_apply_user_restrictions(self):
        """Test method appy_user_restrictions() of SmpProject"""
        permsys = PermissionSystem(self.env)
        projects = self.prjmodel.get_all_projects()

        # Permission provider must give us a permission for each project
        perms = permsys.get_user_permissions()
        for pr_id in range(5):
            self.assertIn(PERM_TEMPLATE % (pr_id + 1), perms)  # PROJECT_<project_id>_MEMBER

        for pr_id in (7, 8):
            self.assertNotIn(PERM_TEMPLATE % pr_id, perms)

        restricted_projects = self.prjmodel.apply_user_restrictions(projects, 'Foo')
        # No permission granted so we only see the unrestricted projects
        self.assertListEqual([2, 3, 5], [prj.id for prj in restricted_projects])

        # Grant user permissions
        for project in projects:
            if project.restricted:
                users = project.description.split()
                for user in users:
                    permsys.grant_permission(user, PERM_TEMPLATE % project.id)

        # Just check if we granted the right permissions
        for project in projects:
            if project.restricted:
                for user in project.description.split():
                    perms = permsys.get_user_permissions(user)
                    self.assertTrue(PERM_TEMPLATE % project.id in perms and perms[PERM_TEMPLATE % project.id])
                    self.assertTrue(PERM_TEMPLATE % 2 not in perms or not perms[PERM_TEMPLATE % 2])

        # restricted_projects holds projects without any restrictions and projects assigned to the given user
        restricted_projects = self.prjmodel.apply_user_restrictions(projects, 'Foo')
        self.assertEqual(6, len(restricted_projects))
        self.assertListEqual([1, 2, 3, 4, 5, 6], [prj.id for prj in restricted_projects])

        restricted_projects = self.prjmodel.apply_user_restrictions(projects, 'Bar')
        self.assertEqual(5, len(restricted_projects))
        self.assertListEqual([1, 2, 3, 5, 6], [prj.id for prj in restricted_projects])

        restricted_projects = self.prjmodel.apply_user_restrictions(projects, 'Baz')
        self.assertEqual(5, len(restricted_projects))
        self.assertListEqual([2, 3, 4, 5, 6], [prj.id for prj in restricted_projects])

        # PÜrojects without set restrictions can be seen by anyone
        restricted_projects = self.prjmodel.apply_user_restrictions(projects, 'BazBaz')
        self.assertEqual(3, len(restricted_projects))
        self.assertListEqual([2, 3, 5], [prj.id for prj in restricted_projects])


class TestSmpProjectUpdate(unittest.TestCase):
    """Test project filtering by permission and user"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        self.prjmodel = SmpProject(self.env)
        self.msmodel = SmpMilestone(self.env)
        self.vermodel = SmpVersion(self.env)
        self.compmodel = SmpComponent(self.env)
        self.env.config.set("ticket-custom", "project", "select")

        self.projects = (("Name: Prj 1", 'Summary 1', 'Foo Bar', None, "YES"),
                         ("Name: Prj 2", 'Summary 2', 'Description 2', None, None),
                         ("Name: Prj 3", 'Summary 3', 'Description 3', None, ""),
                         ("Name: Prj 4", 'Summary 4', 'Baz Foo', None, "YES"),
                         ("Name: Prj 5", 'Summary 5', 'Description 5', None, None),
                         ("Name: Prj 6", 'Summary 6', 'Baz Foo Bar', None, "YES"),
                         )

        for item in self.projects:
            self.prjmodel.add(*item)
        projects = self.prjmodel.get_all_projects()  # populate ticketcustom field data

        self.ticket_data = ("Name: Prj 1", "Name: Prj 2", "Name: Prj 3",
                             "Name: Prj 4", "Name: Prj 5", "Name: Prj 6",
                             "Name: Prj 1", "Name: Prj 2", "Name: Prj 3",
                             "", "", "",
                             "Name: Prj 4", "Name: Prj 5", "Name: Prj 6")
        for data in self.ticket_data:
            tkt = Ticket(self.env)
            tkt['summary'] = data + u' Summary'
            if data:
                tkt['project'] = data
            tkt.insert()

        self.milestones = (("ms 1", 2), ("ms 2", 1), ("ms 3", 2))
        for item in self.milestones:
            self.msmodel.add(*item)

        self.components = (("comp 1", 1), ("comp 2", 3), ("comp 3", 2))
        for item in self.components:
            self.compmodel.add(*item)

        self.versions = (("ver 1", 3), ("ver 2",  2), ("ver 3", 1))
        for item in self.versions:
            self.vermodel.add(*item)

    def tearDown(self):
        self.env.reset_db()

    def test_update_summary(self):
        """Test update of summary"""
        # Check test setup
        projects = self.prjmodel.get_all_projects()
        for project in projects:
            self.assertEqual(project.summary, self.projects[project.id - 1][1])

        # Update projects
        for project in projects:
            summary = "%s Summary %s" % (project.id, project.id)
            self.prjmodel.update(project.id, project.name, summary,
                                 project.description, project.closed, project.restricted)

        projects = self.prjmodel.get_all_projects()
        for project in projects:
            self.assertEqual(project.summary, "%s Summary %s" % (project.id, project.id))

    def test_update_name(self):
        """Test update of summary"""
        # Check test setup
        projects = self.prjmodel.get_all_projects()
        for project in projects:
            self.assertEqual(project.name, self.projects[project.id - 1][0])

        # Check custom field data
        custom_data = defaultdict(list)
        for tcustom in self.env.db_query("""SELECT * FROM ticket_custom"""):
            custom_data[tcustom[2]].append(tcustom[0])  # key is project name, value list of ticket ids
        self.assertEqual(6, len(custom_data))

        project = projects[0]
        old_name = project.name
        new_name = 'New Name here'
        self.prjmodel.update(project.id, new_name, project.summary,
                             project.description, project.closed, project.restricted)

        new_custom_data = defaultdict(list)
        for tcustom in self.env.db_query("""SELECT * FROM ticket_custom"""):
            new_custom_data[tcustom[2]].append(tcustom[0])  # key is project name, value is list of ticket ids
        self.assertEqual(6, len(new_custom_data))

        self.assertListEqual(custom_data[old_name], new_custom_data[new_name])
        self.assertNotIn(old_name, new_custom_data)
        self.assertListEqual([], new_custom_data[old_name])  # works because of defaultdict

        for project in projects:
            name = "%s New Name %s" % (project.id, project.id)
            self.prjmodel.update(project.id, name, project.summary,
                                 project.description, project.closed, project.restricted)

        projects = self.prjmodel.get_all_projects()
        for project in projects:
            self.assertEqual(project.name, "%s New Name %s" % (project.id, project.id))
            self.assertEqual(project.summary, "Summary %s" % (project.id,))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSmpProjectAdd))
    suite.addTest(unittest.makeSuite(TestSmpProjectDelete))
    suite.addTest(unittest.makeSuite(TestSmpProjectExists))
    suite.addTest(unittest.makeSuite(TestSmpProjectGetAllProjects))
    suite.addTest(unittest.makeSuite(TestSmpProjectApplyRestrictions))
    suite.addTest(unittest.makeSuite(TestSmpProjectUpdate))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
