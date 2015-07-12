# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Armin Ronacher <armin.ronacher@active-4.com>
# Copyright (C) 2008 Michael Renzmann <mrenzmann@otaku42.de>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Index, Table
from trac.env import IEnvironmentSetupParticipant

schema_version = 3
schema_version_name = 'tracpaste_version'

schema = [
    Table('pastes', key='id')[
        Column('id', auto_increment=True),
        Column('title'),
        Column('author'),
        Column('mimetype'),
        Column('data'),
        Column('time', type='int'),
        Index(['id']),
        Index(['time'])
    ],
]


class TracpasteSetup(Component):

    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        self.dbm = DatabaseManager(self.env)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        return self.dbm.needs_upgrade(schema_version, schema_version_name)

    def upgrade_environment(self, db=None):
        if self.dbm.get_database_version(schema_version_name) is False and \
                'pastes' in self.dbm.get_table_names():
            self.dbm.set_database_version(1, schema_version_name)

        if self.dbm.get_database_version(schema_version_name) is False:
            self.dbm.create_tables(schema)
            self.dbm.set_database_version(schema_version, schema_version_name)
        else:
            self.dbm.upgrade(schema_version, schema_version_name,
                             'tracpaste.upgrades')
