# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

# SimpleMultiProject.SMP_EnvironmentSetupParticipant

from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.util.text import printout

import simplemultiproject.compat


# Database schema variables
db_version_key = 'simplemultiproject_version'
db_version = 6

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
