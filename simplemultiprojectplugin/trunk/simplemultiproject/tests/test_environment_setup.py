# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 Cinc
#
# License: 3-clause BSD
#
import unittest
from itertools import groupby

from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.perm import PermissionSystem
from trac.test import EnvironmentStub
from simplemultiproject.environmentSetup import db_version_key, smpEnvironmentSetupParticipant
from simplemultiproject.smp_model import SmpComponent, SmpMilestone, SmpProject, SmpVersion
from simplemultiproject.tests.util import revert_schema


tables_v6 = [
    Table('smp_project', key='id_project')[
        Column('id_project', type='integer', auto_increment=True),
        Column('name', type='varchar(255)'),
        Column('description', type='varchar(255)'),
        Column('summary', type='varchar(255)'),
        Column('closed', type='int64'),
        Column('restrict_to')
    ],
    Table('smp_milestone_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('milestone', type='varchar(255)'),
        Column('id_project', type='integer')
    ],
    Table('smp_version_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('version', type='varchar(255)'),
        Column('id_project', type='integer')
    ],
    Table('smp_component_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('component', type='varchar(255)'),
        Column('id_project', type='integer')
    ],
]


def upgrade_environment_to_v6(self):
    print("Preparing database for v6")
    dbm = DatabaseManager(self.env)
    db_installed_version = dbm.get_database_version(db_version_key)

    with self.env.db_transaction as db:
        if db_installed_version < 6:
            dbm.upgrade_tables(tables_v6)
            db_installed_version = 6
            dbm.set_database_version(db_installed_version, db_version_key)


class TestEnvironmentUpgradeClosed(unittest.TestCase):
    """Contents of closed column is changed to None if 0.

    0 is a valid date while None indicates we havn't set a closing data yet. With 0 in the database
    conversion to readable date may yield surprising results, because with None we get the current date, with 0
    1970-01-01.
    """

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            upgrade_environment_to_v6(self.env)
        self.model = SmpProject(self.env)
        self.msmodel = SmpMilestone(self.env)
        self.vermodel = SmpVersion(self.env)
        self.compmodel = SmpComponent(self.env)

        self.projects = (("Name: Prj 1", 'Summary 1', '0', 0, "Foo, Bar"),
                         ("Name: Prj 2", 'Summary 2', 'None', None, None),
                         ("Name: Prj 3", 'Summary 2', '0', 0, None),
                         ("Name: Prj 4", 'Summary 2', '1590758430000000', 1590758430000000, None),
                         ("Name: Prj 5", 'Summary 3', '1595758430000000', 1595758430000000, "!, Foo, Baz"))
        for item in self.projects:
            self.model.add(*item)

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

    def test_closed_field_set_to_none(self):
        """Contents of closed column is changed to None if 0."""
        projects = self.model.get_all_projects()  # sorted by name

        # projects with integer value set, either 0 or other
        for idx in (0, 2, 3, 4):
            self.assertEqual('%s' % projects[idx].closed, projects[idx].description)
        for idx in (1,):
            self.assertIsNone(projects[idx].closed)

        # upgrade to v7
        with self.env.db_transaction as db:
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)

        projects = self.model.get_all_projects()  # sorted by name
        # projects with integer value set, either 0 or other
        for idx in (3, 4):
            self.assertEqual('%s' % projects[idx].closed, projects[idx].description)
        for idx in (0, 1, 2):
            self.assertIsNone(projects[idx].closed)


class TestEnvironmentFieldUpgrade(unittest.TestCase):
    """Database fields are changed from vchar(255) to text during upgrade"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            upgrade_environment_to_v6(self.env)
        self.model = SmpProject(self.env)
        self.msmodel = SmpMilestone(self.env)
        self.vermodel = SmpVersion(self.env)
        self.compmodel = SmpComponent(self.env)

        self.projects = (("Name: Prj 1", 'Summary 1', 'Description 1', None, "Foo, Bar"),
                         ("Name: Prj 2", 'Summary 2', 'Description 2', None, None),
                         ("Name: Prj 3", 'Summary 3', 'Description 3', None, "!, Foo, Baz"))
        for item in self.projects:
            self.model.add(*item)

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

    def test_project_field_change_to_text(self):
        projects = self.model.get_all_projects()  # sorted by name

        # upgrade to v7
        with self.env.db_transaction as db:
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)

        # check fields
        projects_after = self.model.get_all_projects()
        for idx, item in enumerate(projects_after):
            self.assertEqual(item[0], projects[idx][0])
            self.assertEqual(item[1], projects[idx][1])
            self.assertEqual(item[2], projects[idx][2])
            self.assertEqual(item[3], projects[idx][3])
            self.assertEqual(item[4], projects[idx][4])

    def test_milestone_field_change_to_text(self):
        ms = self.msmodel.get_all_milestones_and_id_project_id()  # milestone name and associated project id
        # upgrade to v7
        with self.env.db_transaction as db:
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        # check field contents
        ms_after = self.msmodel.get_all_milestones_and_id_project_id()
        for idx, item in enumerate(ms_after):
            self.assertSequenceEqual(item, ms[idx])

    def test_component_field_change_to_text(self):
        comps = self.compmodel.get_all_components_and_project_id()  # component name and associated project id
        # upgrade to v7
        with self.env.db_transaction as db:
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        # check field contents
        comps_after = self.compmodel.get_all_components_and_project_id()
        for idx, item in enumerate(comps_after):
            self.assertSequenceEqual(item, comps[idx])

    def test_version_field_change_to_text(self):
        vers = self.vermodel.get_all_versions_and_project_id()  # component name and associated project id
        # upgrade to v7
        with self.env.db_transaction as db:
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)
        # check field contents
        vers_after = self.vermodel.get_all_versions_and_project_id()
        for idx, item in enumerate(vers_after):
            self.assertSequenceEqual(item, vers[idx])


class TestEnvironmentUpgradeMigrateRestrictions(unittest.TestCase):
    """With new permission system the field 'restrict_to' has a new meaning"""

    def setUp(self):
        self.env = EnvironmentStub(default_data=True,
                                   enable=["trac.*", "simplemultiproject.*"])
        with self.env.db_transaction as db:
            revert_schema(self.env)
            upgrade_environment_to_v6(self.env)
        self.model = SmpProject(self.env)
        self.msmodel = SmpMilestone(self.env)
        self.vermodel = SmpVersion(self.env)
        self.compmodel = SmpComponent(self.env)

        self.projects = (("Name: Prj 1", 'Summary 1', 'Description 1', None, "Foo, Bar"),
                         ("Name: Prj 2", 'Summary 2', 'Description 2', None, None),
                         ("Name: Prj 3", 'Summary 3', 'Description 3', None, "!, Foo, Baz"),
                         ("Name: Prj 4", 'Summary 4', 'Description 4', None, "Baz,Foo"),
                         ("Name: Prj 5", 'Summary 5', 'Description 5', None, "!,Baz"),
                         ("Name: Prj 6", 'Summary 6', 'Description 6', None, "Baz, Foo,Bar"),
                         )

        for item in self.projects:
            self.model.add(*item)

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

    def test_migrate_restrictions(self):
        # upgrade to v7
        with self.env.db_transaction as db:
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)

        permsys = PermissionSystem(self.env)
        projects = self.model.get_all_projects()
        for idx, item in enumerate(self.projects):
            if item[4]:
                # projects had restrictions before the upgrade
                users = item[4].split(',')
                users = [usr.strip() for usr in users]
                if users[0] == u'!':
                    self.assertEqual(u'YES', projects[idx][5])
                else:
                    # Check if every user from restrict list got project membership
                    for usr in users:
                        perms = permsys.get_user_permissions(usr)
                        self.assertIn("PROJECT_%s_MEMBER" % projects[idx][0], perms, 'Usr: %s, prj ID: %s' %
                                      (usr, projects[idx][0]))

    def test_migrate_restrictions_user_names(self):
        """Test if usernames are without trailing or leading spaces."""
        def _get_users_dict(perm_sys):
            """ This is taken from perm.py (Trac 1.2.6)"""
            perms = sorted((p for p in perm_sys.get_all_permissions()
                            if p[1].isupper()), key=lambda p: p[0])

            return dict((k, sorted(i[1] for i in list(g)))
                        for k, g in groupby(perms, key=lambda p: p[0]))

        # upgrade to v7
        with self.env.db_transaction as db:
            smpEnvironmentSetupParticipant(self.env).upgrade_environment(db)

        permsys = PermissionSystem(self.env)
        names = sorted([u'Foo', u'Bar', u'Baz', u'anonymous', u'authenticated'])

        known_users = sorted(_get_users_dict(permsys))
        self.assertEqual(5, len(known_users))  # there is always anonymour and authenticated
        self.assertListEqual(names, known_users)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestEnvironmentUpgradeClosed))
    suite.addTest(unittest.makeSuite(TestEnvironmentFieldUpgrade))
    suite.addTest(unittest.makeSuite(TestEnvironmentUpgradeMigrateRestrictions))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
