# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Table, Column
from trac.env import IEnvironmentSetupParticipant


class ContactsEnvironment(Component):

    implements(IEnvironmentSetupParticipant)

    db_version_key = 'contacts_version'
    db_version = 1

    contacts_table = [
        Table('contact', key=('id',))[
            Column('id', auto_increment=True),
            Column('first'),
            Column('last'),
            Column('position'),
            Column('email'),
            Column('phone')
        ]
    ]

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(self.db_version, self.db_version_key)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        dbm.create_tables(self.contacts_table)
        dbm.set_database_version(self.db_version, self.db_version_key)
