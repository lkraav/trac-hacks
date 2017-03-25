# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.db import Column, DatabaseManager, Index, Table
from trac.env import IEnvironmentSetupParticipant

# Database version identifier. Used for automatic upgrades.
db_version = 14

##
# Database schema

schema = [
    # root table
    Table('forms', key='id')[
        Column('id', auto_increment=True),
        Column('realm'),
        Column('resource_id'),
        Column('subcontext'),
        Column('state'),
        Column('author'),
        Column('time', type='int'),
        Column('keep_history', type='int'),
        Column('track_fields', type='int'),
        Index(['realm', 'resource_id', 'subcontext'], unique=True),
        Index(['author']),
        Index(['time'])],

    # field changes tracking
    Table('forms_fields')[
        Column('id', type='int'),
        Column('field'),
        Column('author'),
        Column('time', type='int'),
        Index(['id', 'field'], unique=True)],

    # change history
    Table('forms_history')[
        Column('id', type='int'),
        Column('author'),
        Column('time', type='int'),
        Column('old_state'),
        Index(['id']),
        Index(['author']),
        Index(['time'])],
]


def _db_to_version(name):
    return int(name.lstrip('db'))


class DBComponent(Component):
    """Provides TracForms db schema management methods."""

    implements(IEnvironmentSetupParticipant)

    apply_schema = False
    plugin_name = 'forms'

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db=None):
        if not type(self).__dict__.get('apply_schema', False):
            self.log.debug("Not checking schema for \"%s\", since "
                           "apply_schema is not defined or is False.",
                           type(self).__name__)
            return False
        installed = self.get_installed_version()
        for version, fn in self.get_schema_functions():
            if version > installed:
                self.log.debug('"%s" requires a schema upgrade.',
                               type(self).__name__)
                return True
        else:
            self.log.debug('"%s" does not need a schema upgrade.',
                           type(self).__name__)
            return False

    def upgrade_environment(self, db=None):
        if not type(self).__dict__.get('apply_schema', False):
            self.log.debug("Not updating schema for \"%s\" since "
                           "apply_schema is not defined or is False.",
                           type(self).__name__)
            return
        installed = self.get_installed_version()
        if installed is None:
            self.log.info("Installing TracForm plugin schema %s", db_version)
            db_connector = DatabaseManager(self.env).get_connector()[0]
            with self.env.db_transaction as db:
                for table in schema:
                    for stmt in db_connector.to_sql(table):
                        db(stmt)
                self.set_installed_version(db_version)
            self.log.info("Installation of %s successful.", db_version)
            return
        self.log.debug(
            'Upgrading schema for "%s".' % type(self).__name__)
        for version, fn in self.get_schema_functions():
            if version > installed:
                self.log.info("Upgrading TracForm plugin schema to %s",
                              version)
                self.log.info('- %s: %s' % (fn.__name__, fn.__doc__))
                self.set_installed_version(version)
                installed = version
                self.log.info("Upgrade to %s successful.", version)

    # TracForms db schema management methods

    def get_installed_version(self):
        version = self.get_system_value(self.plugin_name + '_version')
        if version is None:
            # check for old naming schema
            oldversion = self.get_system_value('TracFormDBComponent:version')
            version = _db_oldversion_dict.get(oldversion)
        if version is None:
            return version
        return int(version)

    def get_schema_functions(self, prefix='db'):
        fns = []
        for name in self.__dict__:
            if name.startswith(prefix):
                fns.append((_db_to_version(name), getattr(self, name)))
        for cls in type(self).__mro__:
            for name in cls.__dict__:
                if name.startswith(prefix):
                    fns.append((_db_to_version(name), getattr(self, name)))
        fns.sort()
        return tuple(fns)

    def set_installed_version(self, version):
        self.set_system_value(self.plugin_name + '_version', version)

    # Trac db 'system' table management methods for TracForms entry

    def get_system_value(self, key):
        for value, in self.env.db_query("""
                SELECT value FROM system WHERE name=%s
                """, (key,)):
            return value

    def set_system_value(self, key, value):
        """Atomic UPSERT db transaction to save TracForms version."""
        with self.env.db_transaction as db:
            for value, in db("""
                    SELECT value FROM system WHERE name=%s
                    """, (key,)):
                db("""
                    UPDATE system SET value=%s WHERE name=%s
                    """, (value, key))
                break
            else:
                db("""
                    INSERT INTO system(name, value) VALUES(%s, %s)
                    """, (key, value))


_db_oldversion_dict = {
    'dbschema_2008_06_15_0000': 0, 'dbschema_2008_06_15_0001': 1,
    'dbschema_2008_06_14_0002': 2, 'dbschema_2008_06_15_0003': 3,
    'dbschema_2008_06_15_0004': 4, 'dbschema_2008_06_15_0010': 10,
    'dbschema_2008_06_15_0011': 11, 'dbschema_2008_06_15_0012': 12,
}
