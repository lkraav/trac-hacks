# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
# All rights reserved.
#
# The i18n support was added by Steffen Hoffmann <hoff.st@web.de>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# For a copy of the GNU General Public License see
# <http://www.gnu.org/licenses/>.

from trac.core import Component, TracError, implements
from trac.db import Table, Column, DatabaseManager
from trac.env import IEnvironmentSetupParticipant


class WatchlistDataBaseUpgrader(Component):
    """DataBase module for the Trac WatchlistPlugin.
       Handles creation and upgrading of watchlist DB tables."""

    implements(IEnvironmentSetupParticipant)

    latest_version = 4

    watchlist_table = Table('watchlist', key=['wluser', 'realm', 'resid'])[
        Column('wluser'),
        Column('realm'),
        Column('resid'),
        Column('lastvisit', type='int64'),
    ]
    settings_table = Table('watchlist_settings', key=['wluser', 'name'])[
        Column('wluser'),
        Column('name'),
        Column('type'),
        Column('settings'),
    ]

    def environment_created(self):
        """Creates watchlist tables when a new Trac environment is created.
        """
        with self.env.db_transaction:
            self.create_watchlist_table()
            self.create_settings_table()
            self.set_version(self.latest_version)

    def environment_needs_upgrade(self, db=None):
        """Tests if watchlist tables must be upgraded."""
        if not self.table_exists('watchlist') or \
                not self.table_exists('watchlist_settings'):
            return True
        version = self.get_version()
        if version < self.latest_version:
            return True
        elif version > self.latest_version:
            raise TracError("Watchlist DB table version newer than plug-in "
                            "version")
        return False

    def upgrade_environment(self, db=None):
        """Upgrades all watchlist tables to current version."""
        with self.env.db_transaction:
            old_version = self.get_version()
            self.upgrade_watchlist_table(old_version, self.latest_version)
            self.upgrade_settings_table(old_version, self.latest_version)
            self.set_version(self.latest_version)

    def upgrade_watchlist_table(self, old_version, new_version):
        """Upgrades watchlist table to current version."""
        self.log.info("Attempting upgrade of watchlist table from v%i to v%i",
                      old_version, new_version)
        if not self.table_exists('watchlist'):
            self.create_watchlist_table()
            return
        if old_version == new_version:
            return
        try:
            upgrader = getattr(self, 'upgrade_watchlist_table_from_v%i_to_v%i'
                                     % (old_version, new_version))
        except AttributeError:
            raise TracError("Requested watchlist table version " + unicode(
                new_version) + " not supported for upgrade")

        upgrader()

    def upgrade_settings_table(self, old_version, new_version):
        """Upgrades watchlist_settings table to current version."""
        self.log.info("Attempting upgrade of watchlist table from v%i to v%i",
                      old_version, new_version)

        if not self.table_exists('watchlist_settings'):
            self.create_settings_table()
            return

        if old_version == new_version:
            return

        if old_version < 4:
            self.upgrade_settings_table_to_v4()
            old_version = 4
            if new_version == 4:
                return

        # Code for future versions > 4
        try:
            upgrader = getattr(self, 'upgrade_settings_table_from_v%i_to_v%i'
                                     % (old_version, new_version))
        except AttributeError:
            raise TracError("Requested settings table version " + unicode(
                new_version) + " not supported for upgrade")

        upgrader()
        raise NotImplemented

    def get_version(self):
        """Returns watchlist table version from system table or 0 if not
        present.
        """
        try:
            for value, in self.env.db_query("""
                    SELECT value FROM system WHERE name='watchlist_version'
                    """):
                return int(value)
        except (AttributeError, TypeError):
            self.log.info("No value for 'watchlist_version' found in "
                          "'system' table")
            return 0
        except ValueError, e:
            self.log.error("Invalid value found for 'watchlist_version' "
                           "found in system table: %s", e)
            self.log.info("Value for 'watchlist_version' will be set to 0")
            self.set_version(0)
            return 0
        except Exception, e:
            self.log.error("Unknown error when trying to read "
                           "'watchlist_version' from 'system' table: %s", e)
            self.log.info("Value for 'watchlist_version' will be set to 0")
            self.set_version(0)
            return 0

    def set_version(self, version):
        """Sets watchlist table version in the system table."""
        try:
            version = int(version)
        except ValueError:
            raise ValueError("Version must be an integer")
        try:
            self.env.db_transaction("""
                DELETE FROM system WHERE name='watchlist_version'
                """)
        except Exception as e:
            self.log.warn(unicode(e))
        try:
            self.env.db_transaction("""
                INSERT INTO system (name,value)
                VALUES ('watchlist_version',%s)
                """, (unicode(version),))
        except Exception as e:
            self.log.error("Could not set watchlist_version: %s", e)
            raise

    def create_watchlist_table(self):
        db_connector = DatabaseManager(self.env).get_connector()[0]
        self.log.info("Creating 'watchlist' table in version %s",
                      self.latest_version)

        with self.env.db_transaction as db:
            for statement in db_connector.to_sql(self.watchlist_table):
                db(statement)

    def create_settings_table(self):
        db_connector = DatabaseManager(self.env).get_connector()[0]
        self.log.info("Creating 'watchlist_setting' table in version %s",
                      self.latest_version)

        with self.env.db_transaction as db:
            for statement in db_connector.to_sql(self.settings_table):
                db(statement)

    def table_exists(self, table):
        if table in self._get_tables():
            return True
        return False  # This is a new installation.

    def upgrade_watchlist_table_from_v0_to_v4(self):
        self.upgrade_watchlist_table_to_v4('*')

    def upgrade_watchlist_table_from_v1_to_v4(self):
        self.upgrade_watchlist_table_to_v4('*')

    def upgrade_watchlist_table_from_v2_to_v4(self):
        """Upgrades watchlist table from v2 which has four columns. The
        forth was 'notify' which was dropped again quickly.
        """
        self.upgrade_watchlist_table_to_v4('wluser,realm,resid')

    def upgrade_watchlist_table_from_v3_to_v4(self):
        self.upgrade_watchlist_table_to_v4('*')

    def upgrade_watchlist_table_to_v4(self, selection):
        """Upgrade 'watchlist' table to v4. The data is copied into a
        temporary table and then back into the newly created table.
        """
        db_connector = DatabaseManager(self.env).get_connector()[0]

        # Temporary name for new watchlist table
        new_table = self.watchlist_table
        new_table.name = 'watchlist_new'

        # Delete new table if it should exists because of a aborted previous
        # upgrade attempt
        try:
            self.env.db_transaction("DROP TABLE watchlist_new")
        except:
            pass

        with self.env.db_transaction as db:
            # Create new table
            for statement in db_connector.to_sql(new_table):
                db(statement)

            # Copy existing data to it
            db("""
                INSERT INTO watchlist_new
                SELECT DISTINCT %s FROM watchlist
                """ % selection)

            # Delete only table
            db("DROP TABLE watchlist")

            # Rename table
            db("ALTER TABLE watchlist_new RENAME TO watchlist")

        self.log.info("Upgraded 'watchlist' table to version 4")

    def upgrade_settings_table_to_v4(self):
        """Upgrades 'watchlist_settings' table to v4.
           This table did not existed in v0-v2, so there is only v3
           to handle."""
        db_connector = DatabaseManager(self.env).get_connector()[0]

        # Delete new table if it should exists because of a aborted previous
        # upgrade attempt
        try:
            self.env.db_transaction("DROP TABLE watchlist_settings_new")
        except:
            pass

        # Temporary name for new watchlist_settings table
        new_table = self.settings_table
        new_table.name = 'watchlist_settings_new'

        with self.env.db_transaction as db:
            # Create new table
            for statement in db_connector.to_sql(new_table):
                db(statement)

            # Copy existing data to it
            db("""
                INSERT INTO watchlist_settings_new (wluser,settings)
                SELECT DISTINCT wluser,settings FROM watchlist_settings
                """)

            # Delete only table
            db("DROP TABLE watchlist_settings")

            # Rename table
            db("""
                ALTER TABLE watchlist_settings_new
                RENAME TO watchlist_settings
                """)

            # Set new columns to default value
            db("""
                UPDATE watchlist_settings
                SET name='booloptions', type='ListOfBool'
                """)

        self.log.info("Upgraded 'watchlist_settings' table to version 4")

    def _get_tables(self):
        """Code from TracMigratePlugin by Jun Omae (see tracmigrate.admin)."""
        dburi = self.config.get('trac', 'database')
        if dburi.startswith('sqlite:'):
            sql = """
                SELECT name
                  FROM sqlite_master
                 WHERE type='table'
                   AND NOT name='sqlite_sequence'
            """
        elif dburi.startswith('postgres:'):
            sql = """
                SELECT tablename
                  FROM pg_tables
                 WHERE schemaname = ANY (current_schemas(false))
            """
        elif dburi.startswith('mysql:'):
            sql = "SHOW TABLES"
        else:
            raise TracError('Unsupported database type "%s"'
                            % dburi.split(':')[0])
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute(sql)
            return sorted(row[0] for row in cursor)
