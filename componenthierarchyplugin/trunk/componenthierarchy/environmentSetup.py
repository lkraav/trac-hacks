# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering, falkb
#
from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, DatabaseManager


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
        # Initialise database schema version tracking.
        cursor = db.cursor()
        # Get currently installed database schema version
        db_installed_version = 0
        try:
            sqlGetInstalledVersion = "SELECT value FROM system WHERE name = '%s'" % db_version_key
            cursor.execute(sqlGetInstalledVersion)
            db_installed_version = int(cursor.fetchone()[0])
        except:
            # No version currently, inserting new one.
            db_installed_version = 0
            
        # return boolean for if we need to update or not
        needsUpgrade = (db_installed_version < db_version)
        if needsUpgrade:
            print "ComponentHierarchy database schema version: %s initialized." % db_version
            print "ComponentHierarchy database schema version: %s installed." % db_installed_version
            print "ComponentHierarchy database schema is out of date: %s" % needsUpgrade
        return needsUpgrade


    def upgrade_environment(self, db):
        print "Upgrading ComponentHierarchy database schema"
        cursor = db.cursor()

        db_installed_version = 0
        try:
            sqlGetInstalledVersion = "SELECT value FROM system WHERE name = '%s'" % db_version_key
            cursor.execute(sqlGetInstalledVersion)
            db_installed_version = int(cursor.fetchone()[0])
        except:
            print "Upgrading ComponentHierarchy database schema"
            
        db_connector, _ = DatabaseManager(self.env)._get_connector()

        if db_installed_version < 1:
            # Create tables
            for table in tables_v1:
                for statement in db_connector.to_sql(table):
                    cursor.execute(statement)
                    
            sqlInsertVersion = "INSERT INTO system (name, value) VALUES ('%s','%s')" % (db_version_key, db_version)
            cursor.execute(sqlInsertVersion)
            db_installed_version = 1
