# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Malcolm Studd <mestudd@gmail.com>
# Copyright (C) 2012-2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component, TracError, implements
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import _

db_version = 1
name = 'extended_version_plugin'

schema = [
    Table('milestone_version', key='milestone')[
        Column('milestone'),
        Column('version'),
    ]
]


def to_sql(env, table):
    from trac.db.api import DatabaseManager
    dc = DatabaseManager(env).get_connector()[0]
    return dc.to_sql(table)


def create_tables(env):
    with env.db_transaction as db:
        for table in schema:
            for stmt in to_sql(env, table):
                db(stmt)
        db("""
            INSERT into system values (%s, %s)
            """, (name, db_version))


class ExtendedVersionsSetup(Component):
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        # Don't need to do anything when the environment is created
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        current_version = self._get_version()

        if current_version == db_version:
            return False
        elif current_version > db_version:
            raise TracError(_("Database newer than ExtendedVersionPlugin"
                              " version"))
        self.log.info("ExtendedVersionPlugin schema version is %d, should"
                      " be %d", current_version, db_version)
        return True

    def upgrade_environment(self, db=None):
        current_version = self._get_version()

        if current_version == 0:
            create_tables(self.env)
        else:
            pass

    # Internal methods

    def _get_version(self):
        try:
            for value, in self.env.db_query("""
                    SELECT value FROM system WHERE name=%s
                    """, (name,)):
                return int(value)
            else:
                return 0
        except:
            return 0
