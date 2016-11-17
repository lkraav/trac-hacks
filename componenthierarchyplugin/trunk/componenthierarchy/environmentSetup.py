# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering, falkb
#

from trac.core import *
from trac.db import Column, DatabaseManager, Table
from trac.env import IEnvironmentSetupParticipant


# Database schema variables
db_version_key = 'component_hierarchy'
db_version = 1

tables_v1 = [
    Table('component_hierarchy', key = 'component') [
        Column('component', type = 'varchar'),
        Column('parent_component',type = 'varchar')
    ],
]

class ComponentHierarchyEnvironmentSetupParticipant(Component):

    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        db_installed_version = self._get_db_version(db)
        return db_installed_version < db_version

    def upgrade_environment(self, db):
        """Create tables."""
        cursor = db.cursor()
        db_connector = DatabaseManager(self.env)._get_connector()[0]
        for table in tables_v1:
            for statement in db_connector.to_sql(table):
                cursor.execute(statement)
        cursor.execute("""
            INSERT INTO system (name,value) VALUES (%s,%s)
            """, (db_version_key, db_version))

    def _get_db_version(self, db):
        """Get currently installed database schema version."""
        version = 0
        cursor = db.cursor()
        try:
            cursor.execute("SELECT value FROM system WHERE name=%s",
                           (db_version_key,))
            version = int(cursor.fetchone()[0])
        except:
            version = 0
        return version
