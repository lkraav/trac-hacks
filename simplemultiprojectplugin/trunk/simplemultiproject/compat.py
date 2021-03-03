# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# Copyright (C) 2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from __future__ import with_statement

from trac.core import TracError
from trac.db.api import DatabaseManager
from trac.db.schema import Table
from trac.util.translation import _


# For migrating away from Genshi
class JTransformer(object):
    """Class modelled after the Genshi Transformer class. Instead of an xpath it uses a
       selector usable by jQuery.
       You may use cssify (https://github.com/santiycr/cssify) to convert a xpath to a selector."""

    def __init__(self, xpath):
        self.css = xpath  # xpath must be a css selector for jQuery

    def after(self, html):
        return {'pos': 'after', 'css': self.css, 'html': html}

    def before(self, html):
        return {'pos': 'before', 'css': self.css, 'html': html}

    def prepend(self, html):
        return {'pos': 'prepend', 'css': self.css, 'html': html}

    def append(self, html):
        return {'pos': 'append', 'css': self.css, 'html': html}

    def remove(self):
        return {'pos': 'remove', 'css': self.css, 'html': ''}

    def replace(self, html):
        return {'pos': 'replace', 'css': self.css, 'html': html}

# Methods backported from Trac 1.2

if not hasattr(DatabaseManager, 'drop_tables'):
    def drop_tables(self, schema):
        """Drop the specified tables.

        :param schema: an iterable of `Table` objects or table names.

        :since: version 1.0.2
        """
        with self.env.db_transaction as db:
            for table in schema:
                table_name = table.name if isinstance(table, Table) else table
                db.drop_table(table_name)
    DatabaseManager.drop_tables = drop_tables


if not hasattr(DatabaseManager, 'insert_into_tables'):
    def insert_into_tables(self, data_or_callable):
        """Insert data into existing tables.

        :param data_or_callable: Nested tuples of table names, column names
                                 and row data:
                                 (table1,
                                  (column1, column2),
                                  ((row1col1, row1col2), (row2col1, row2col2)),
                                  table2, ...)
                                or a callable that takes a single parameter
                                `db` and returns the aforementioned nested
                                tuple.
        :since: version 1.1.3
        """
        with self.env.db_transaction as db:
            data = data_or_callable(db) if callable(data_or_callable) \
                                        else data_or_callable
            for table, cols, vals in data:
                db.executemany("INSERT INTO %s (%s) VALUES (%s)"
                               % (table, ','.join(cols),
                                  ','.join(['%s'] * len(cols))), vals)
    DatabaseManager.insert_into_tables = insert_into_tables


if not hasattr(DatabaseManager, 'create_tables'):
    def create_tables(self, schema):
        """Create the specified tables.

        :param schema: an iterable of table objects.

        :since: version 1.0.2
        """
        connector = self.get_connector()[0]
        with self.env.db_transaction as db:
            for table in schema:
                for sql in connector.to_sql(table):
                    db(sql)
    DatabaseManager.create_tables = create_tables


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


if not hasattr(DatabaseManager, 'get_column_names'):
    def get_column_names(self, table):
        """Returns a list of the column names for `table`.

        :param table: a `Table` object or table name.

        :since: 1.2
        """
        table_name = table.name if isinstance(table, Table) else table
        with self.env.db_query as db:
            if not self.has_table(table_name):
                raise self.env.db_exc.OperationalError('Table %s not found' %
                                                       db.quote(table_name))
            return db.get_column_names(table_name)
    DatabaseManager.get_column_names = get_column_names


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


if not hasattr(DatabaseManager, 'upgrade'):
    def upgrade(self, version, name='database_version', pkg=None):
        """Invokes `do_upgrade(env, version, cursor)` in module
        `"%s/db%i.py" % (pkg, version)`, for each required version upgrade.

        :param version: the expected integer database version.
        :param name: the name of the entry in the SYSTEM table that contains
                     the database version. Defaults to `database_version`,
                     which contains the database version for Trac.
        :param pkg: the package containing the upgrade modules.

        :raises TracError: if the package or module doesn't exist.
        """
        dbver = self.get_database_version(name)
        for i in range(dbver + 1, version + 1):
            module = 'db%i' % i
            try:
                upgrades = __import__(pkg, globals(), locals(), [module])
            except ImportError:
                raise TracError(_("No upgrade package %(pkg)s", pkg=pkg))
            try:
                script = getattr(upgrades, module)
            except AttributeError:
                raise TracError(_("No upgrade module %(module)s.py",
                                  module=module))
            with self.env.db_transaction as db:
                cursor = db.cursor()
                script.do_upgrade(self.env, i, cursor)
                self.set_database_version(i, name)
    DatabaseManager.upgrade = upgrade


if not hasattr(DatabaseManager, 'upgrade_tables'):
    def upgrade_tables(self, new_schema):
        """Upgrade table schema to `new_schema`, preserving data in
        columns that exist in the current schema and `new_schema`.

        :param new_schema: tuple or list of `Table` objects

        :since: version 1.2
        """
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for new_table in new_schema:
                temp_table_name = new_table.name + '_old'
                has_table = self.has_table(new_table)
                if has_table:
                    old_column_names = set(self.get_column_names(new_table))
                    new_column_names = {col.name for col in new_table.columns}
                    column_names = old_column_names & new_column_names
                    if column_names:
                        cols_to_copy = ','.join(db.quote(name)
                                                for name in column_names)
                        cursor.execute("""
                            CREATE TEMPORARY TABLE %s AS SELECT * FROM %s
                            """ % (db.quote(temp_table_name),
                                   db.quote(new_table.name)))
                    self.drop_tables((new_table,))
                self.create_tables((new_table,))
                if has_table and column_names:
                    cursor.execute("""
                        INSERT INTO %s (%s) SELECT %s FROM %s
                        """ % (db.quote(new_table.name), cols_to_copy,
                               cols_to_copy, db.quote(temp_table_name)))
                    for col in new_table.columns:
                        if col.auto_increment:
                            db.update_sequence(cursor, new_table.name,
                                               col.name)
                    self.drop_tables((temp_table_name,))
    DatabaseManager.upgrade_tables = upgrade_tables


if not hasattr(DatabaseManager, 'has_table'):
    def has_table(self, table):
        table_name = table.name if isinstance(table, Table) else table
        names = self.get_table_names()
        if table_name in names:
            return True
        else:
            return False

    DatabaseManager.has_table = has_table
