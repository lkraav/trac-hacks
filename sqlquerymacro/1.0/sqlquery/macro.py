# -*- coding: utf-8 -*-

import inspect
import re

from trac.config import Option
from trac.core import Component, implements
from trac.db.api import DatabaseManager, get_column_names
from trac.util.html import tag
from trac.wiki.macros import IWikiMacroProvider


class SqlQueryMacro(Component):
    """
    A macro to execute an SQL query against a
    configured database and render the results
    in a table.

    Example:
    {{{
    [[SQL(SELECT * FROM component)]]
    }}}
    """

    implements(IWikiMacroProvider)

    uri = Option("sqlquery", "uri",
        doc="""Database URI to connect to and use for SQL Queries""")

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'SQL'

    def get_macro_description(self, name):
        return inspect.getdoc(self.__class__)

    def expand_macro(self, formatter, name, args):
        if args is None:
            return "No query defined!"

        sql = unicode(args).strip()
        if not re.match(r'\s*SELECT\s', sql, re.I):
            raise ValueError('Only SELECT query is allowed')

        def execute_query(cnx):
            cursor = cnx.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            fields = get_column_names(cursor)
            return records, fields

        if self.uri:
            dbm = SqlQueryDatabaseManager(self.env)
            connector, kwargs = dbm.get_connector()
            cnx = connector.get_connection(**kwargs)
            try:
                records, fields = execute_query(cnx)
            finally:
                cnx.rollback()
                cnx.close()
        else:
            with self.env.db_query as db:
                records, fields = execute_query(db)

        if not records:
            return tag.div('No results')

        try:
            group_idx = fields.index('__group__')
        except ValueError:
            groups = {None: records}
            group_vals = [None]
        else:
            groups = {}
            group_vals = []
            for record in records:
                group = record[group_idx]
                if group not in groups:
                    group_vals.append(group)
                    groups[group] = []
                groups[group].append(record)

        div = tag.div()
        for group in group_vals:
            if group is not None:
                div.append(tag.h3(group))
            table = tag.table(class_='wiki')
            thead = tag.thead(tag.tr(tag.th(field)
                              for field in fields
                              if field not in ('__color__', '__group__')))
            tbody = tag.tbody()
            for record in groups[group]:
                cells = []
                style = None
                for idx, field in enumerate(fields):
                    value = record[idx]
                    if field == '__color__':
                        if isinstance(value, basestring) and ';' not in value:
                            style = 'background-color:' + value
                        continue
                    if field == '__group__':
                        continue
                    if value is None:
                        cell = tag.td('NULL')
                    elif isinstance(value, (int, long, float)):
                        cell = tag.td('%g' % value, style='text-align:right')
                    else:
                        cell = tag.td(value)
                    cells.append(cell)
                tbody.append(tag.tr(cells, style=style))
            table.append([thead, tbody])
            div.append(table)
        return div


class SqlQueryDatabaseManager(DatabaseManager):

    @property
    def connection_uri(self):
        return SqlQueryMacro(self.env).uri
