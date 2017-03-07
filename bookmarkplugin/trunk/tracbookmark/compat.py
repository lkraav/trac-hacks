# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2017 Edgewall Software
# Copyright (C) 2017 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

# Methods backported from Trac 1.2

from trac.core import TracError
from trac.db.api import DatabaseManager
from trac.db.schema import Table
from trac.util.translation import _


if not hasattr(DatabaseManager, 'get_database_version'):
    def get_database_version(self, name='database_version'):
        """Returns the database version from the SYSTEM table as an int,
        or `False` if the entry is not found.

        :param name: The name of the entry that contains the database version
                     in the SYSTEM table. Defaults to `database_version`,
                     which contains the database version for Trac.
        """
        rows = self.env.db_query("""
                SELECT value FROM system WHERE name=%s
                """, (name,))
        return int(rows[0][0]) if rows else False
    DatabaseManager.get_database_version = get_database_version


if not hasattr(DatabaseManager, 'set_database_version'):
    def set_database_version(self, version, name='database_version'):
        """Sets the database version in the SYSTEM table.

        :param version: an integer database version.
        :param name: The name of the entry that contains the database version
                     in the SYSTEM table. Defaults to `database_version`,
                     which contains the database version for Trac.
        """
        current_database_version = self.get_database_version(name)
        if current_database_version is False:
            self.env.db_transaction("""
                    INSERT INTO system (name, value) VALUES (%s, %s)
                    """, (name, version))
        else:
            self.env.db_transaction("""
                    UPDATE system SET value=%s WHERE name=%s
                    """, (version, name))
            self.log.info("Upgraded %s from %d to %d",
                          name, current_database_version, version)
    DatabaseManager.set_database_version = set_database_version


if not hasattr(DatabaseManager, 'get_table_names'):
    def get_table_names(self):
        dburi = self.config.get('trac', 'database')
        if dburi.startswith('sqlite:'):
            query = "SELECT name FROM sqlite_master" \
                    " WHERE type='table' AND NOT name='sqlite_sequence'"
        elif dburi.startswith('postgres:'):
            query = "SELECT tablename FROM pg_tables" \
                    " WHERE schemaname = ANY (current_schemas(false))"
        elif dburi.startswith('mysql:'):
            query = "SHOW TABLES"
        else:
            raise TracError('Unsupported %s database' % dburi.split(':')[0])
        return sorted(row[0] for row in self.env.db_transaction(query))
    DatabaseManager.get_table_names = get_table_names


if not hasattr(DatabaseManager, 'needs_upgrade'):
    def needs_upgrade(self, version, name='database_version'):
        """Checks the database version to determine if an upgrade is needed.

        :param version: the expected integer database version.
        :param name: the name of the entry in the SYSTEM table that contains
                     the database version. Defaults to `database_version`,
                     which contains the database version for Trac.

        :return: `True` if the stored version is less than the expected
                  version, `False` if it is equal to the expected version.
        :raises TracError: if the stored version is greater than the expected
                           version.
        """
        dbver = self.get_database_version(name)
        if dbver == version:
            return False
        elif dbver > version:
            raise TracError(_("Need to downgrade %(name)s.", name=name))
        self.log.info("Need to upgrade %s from %d to %d",
                      name, dbver, version)
        return True
    DatabaseManager.needs_upgrade = needs_upgrade
