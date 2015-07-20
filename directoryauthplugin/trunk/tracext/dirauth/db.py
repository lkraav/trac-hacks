# -*- coding: utf-8 -*-
"""
DirectoryAuthPlugin :: database management part.

License: BSD

(c) 2012 branson matheson branson-dot-matheson-at-nasa-dot-gov
"""

from trac.core import Component, implements
from trac.db.schema import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant

__all__ = ['DirectoryAuthPluginSetup']

# Database version identifier for upgrades.
db_version = 1

# Database schema
schema = [
    # Blog posts
    Table('dir_cache', key='id')[
        Column('id', type='varchar(32)'),
        Column('lut', type='int'),
        Column('data', type='blob'),
        Index(['id'])],
]

schemaPostgres = [
    # Blog posts
    Table('dir_cache', key='id')[
        Column('id', type='varchar(32)'),
        Column('lut', type='int'),
        Column('data', type='bytea'),
        Index(['id'])],
]


upgrade_map = {}


def to_sql(env, table):
    """ Convenience function to get the to_sql for the active connector."""
    from trac.db.api import DatabaseManager
    dc = DatabaseManager(env)._get_connector()[0]
    return dc.to_sql(table)


def create_tables(env, db):
    """ Creates the basic tables as defined by schema.
    using the active database connector. """
    cursor = db.cursor()
    usedSchema = schema
    if env.config.get('trac', 'database').startswith('postgres'):
        usedSchema = schemaPostgres
    for table in usedSchema:
        for stmt in to_sql(env, table):
            cursor.execute(stmt)
    cursor.execute("INSERT into system values ('dirauthplugin_version', %s)",
                   (db_version,))


class DirectoryAuthPluginSetup(Component):

    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        return self._get_version(db) != db_version

    def upgrade_environment(self, db):
        current_ver = self._get_version(db)
        if current_ver == 0:
            create_tables(self.env, db)
        else:
            while current_ver + 1 <= db_version:
                upgrade_map[current_ver + 1](self.env, db)
                current_ver += 1
            cursor = db.cursor()
            cursor.execute("""
                UPDATE system SET value=%s WHERE name='dirauthplugin_version'
                """, db_version)

    def _get_version(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("""
                SELECT value FROM system WHERE name='dirauthplugin_version'
                """)
            for row in cursor:
                return int(row[0])
            return 0
        except:
            return 0
