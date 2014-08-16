# -*- coding: utf-8 -*-

import pkg_resources

from trac.db.api import DatabaseManager
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider

from timetracking.model import SCHEMA


PLUGIN_NAME = 'TimeTrackingPlugin'
PLUGIN_VERSION = 2


class TimeTrackingModule(Component):
    """Time estimations and logging."""

    implements(IPermissionRequestor, IEnvironmentSetupParticipant, ITemplateProvider)

    # IPermissionRequestor methods
    
    def get_permission_actions(self):
        return ['TIME_TRACKING']

    # IEnvironmentSetupParticipant

    def environment_created(self):
        db_connector, _ = DatabaseManager(self.env).get_connector()
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in SCHEMA:
                for stmt in db_connector.to_sql(table): 
                    cursor.execute(stmt) 
            cursor.execute(""" 
                INSERT INTO system (name, value) 
                VALUES (%s, %s) 
                """, (PLUGIN_NAME, PLUGIN_VERSION)) 

    def environment_needs_upgrade(self, db):
        dbver = self.get_db_version()
        if dbver == PLUGIN_VERSION:
            return False
        elif dbver > PLUGIN_VERSION:
            self.env.log.info("%s database schema version is %s, should be %s",
                         PLUGIN_NAME, dbver, PLUGIN_VERSION)
        return True

    def upgrade_environment(self, db):
        db_connector, _ = DatabaseManager(self.env).get_connector() 
        cursor = db.cursor()
        dbver = self.get_db_version()
        if dbver == 0:
            self.env.log.info("Initialize %s database schema to version %s",
                         PLUGIN_NAME, PLUGIN_VERSION)
            for table in SCHEMA:
                for stmt in db_connector.to_sql(table):
                    cursor.execute(stmt)
            cursor.execute("""
                INSERT INTO system (name, value)
                VALUES (%s, %s)
                """, (PLUGIN_NAME, PLUGIN_VERSION))
        else:
            while dbver != PLUGIN_VERSION:
                dbver = dbver + 1
                self.env.log.info("Upgrade %s database schema to version %s",
                         PLUGIN_NAME, dbver)
                modulename = 'db%i' % dbver
                upgrades = __import__('timetracking.upgrades', globals(), locals(), [modulename])
                script = getattr(upgrades, modulename)
                script.do_upgrade(self.env, dbver, cursor)
            cursor.execute("""
                UPDATE system
                SET value=%s
                WHERE name=%s
                """, (PLUGIN_VERSION, PLUGIN_NAME))

    def get_db_version(self):
        rows = self.env.db_query("""
                SELECT value FROM system WHERE name='%s'
                """ % PLUGIN_NAME)
        return int(rows[0][0]) if rows else 0

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('timetracking', pkg_resources.resource_filename('timetracking', 'htdocs'))]

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('timetracking', 'templates')]

