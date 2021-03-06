# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2020 Cinc-th
#

from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionSystem
from trac.util.text import printout

from simplemultiproject.smp_model import SmpProject
import simplemultiproject.compat


# Database schema variables
db_version_key = 'simplemultiproject_version'
db_version = 7

tables = [
    Table('smp_project', key='id_project')[
        Column('id_project', type='integer', auto_increment=True),
        Column('name', type='varchar(255)'),
        Column('description', type='varchar(255)')
    ],
    Table('smp_milestone_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('milestone', type='varchar(255)'),
        Column('id_project', type='integer')
    ],
]

tables_v2 = [
    Table('smp_version_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('version', type='varchar(255)'),
        Column('id_project', type='integer')
    ],
]

tables_v3 = [
    Table('smp_component_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('component', type='varchar(255)'),
        Column('id_project', type='integer')
    ],
]

tables_v6 = [
    Table('smp_project', key='id_project')[
        Column('id_project', type='integer', auto_increment=True),
        Column('name', type='varchar(255)'),
        Column('description', type='varchar(255)'),
        Column('summary', type='varchar(255)'),
        Column('closed', type='int64'),
        Column('restrict_to')
    ],
]

tables_v7 = [
    Table('smp_project', key='id_project')[
        Column('id_project', type='integer', auto_increment=True),
        Column('name', type='text'),
        Column('description', type='text'),
        Column('summary', type='text'),
        Column('closed', type='int64'),
        Column('restrict_to')
    ],
    Table('smp_milestone_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('milestone', type='text'),
        Column('id_project', type='integer')
    ],
    Table('smp_version_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('version', type='text'),
        Column('id_project', type='integer')
    ],
    Table('smp_component_project', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('component', type='text'),
        Column('id_project', type='integer')
    ],
]

class smpEnvironmentSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        dbm = DatabaseManager(self.env)
        db_installed_version = dbm.get_database_version(db_version_key)
        return db_installed_version < db_version

    def upgrade_environment(self, db=None):
        printout("Upgrading SimpleMultiProject database schema")
        dbm = DatabaseManager(self.env)
        db_installed_version = dbm.get_database_version(db_version_key)

        migrate_restrictions = False

        with self.env.db_transaction as db:
            if db_installed_version < 1:
                dbm.create_tables(tables)
                db_installed_version = 1
                dbm.set_database_version(db_installed_version, db_version_key)

            if db_installed_version < 2:
                dbm.create_tables(tables_v2)
                db_installed_version = 2
                dbm.set_database_version(db_installed_version, db_version_key)

            if db_installed_version < 3:
                dbm.create_tables(tables_v3)
                db_installed_version = 3
                dbm.set_database_version(db_installed_version, db_version_key)

            if db_installed_version < 4:
                db("""
                    ALTER TABLE smp_project ADD summary varchar(255)
                    """)
                db_installed_version = 4
                dbm.set_database_version(db_installed_version, db_version_key)

            if db_installed_version < 5:
                db("""
                    ALTER TABLE smp_project ADD closed integer
                    """)
                db("""
                    ALTER TABLE smp_project ADD %s text
                    """ % db.quote('restrict'))
                db_installed_version = 5
                dbm.set_database_version(db_installed_version, db_version_key)

            if db_installed_version < 6:
                dbm.upgrade_tables(tables_v6)
                db_installed_version = 6
                dbm.set_database_version(db_installed_version, db_version_key)

            if db_installed_version < 7:
                dbm.upgrade_tables(tables_v7)
                # Change 'closed' from 0 to None. = is a valid date while None indicates we haven't set a date yet.
                projects = db("""SELECT id_project,name,summary,description,closed,restrict_to
                                 FROM smp_project WHERE closed = 0""")
                for project in projects:
                    db("""UPDATE smp_project
                          SET name=%s, summary=%s, description=%s, closed=%s, restrict_to=%s
                          WHERE id_project=%s""", (project[1], project[2], project[3], None,
                                                   project[5], project[0]))

                db_installed_version = 7
                dbm.set_database_version(db_installed_version, db_version_key)
                migrate_restrictions = True

        # A new oermission system is in place which uses Trac permissions instead of private user lists
        if migrate_restrictions:
            permsys = PermissionSystem(self.env)
            model = SmpProject(self.env)
            projects = model.get_all_projects()
            not_migrated = []

            for project in projects:
                if project.restricted:
                    users = project.restricted.split(',')
                    model.update(*project[:-1], restrict_to='YES')
                    if users[0].strip() == u'!':
                        not_migrated.append(project)
                    else:
                        for usr in users:
                            permsys.grant_permission(usr.strip(), "PROJECT_%s_MEMBER" % project.id)

            for project in not_migrated:
                printout("CAUTION: Project '%s' uses unsupported negated permissions: '%s'." %
                         (project.name, project.restricted),
                         "The project is now set to 'restricted' but no users are associated after "
                         "the upgrade.")
