# -*- coding: utf-8 -*-

import inspect
from StringIO import StringIO

from trac.config import Option
from trac.core import *
from trac.db.api import get_column_names
from trac.web.chrome import web_context
from trac.wiki.macros import IWikiMacroProvider
from trac.wiki.formatter import format_to_html

try:
    from pymills.db import Connection
except ImportError:
    from pymills.dbapi import Connection
from pymills.datatypes import OrderedDict
from pymills.table import Table, Header, Row, Cell


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

        sql = str(args).strip()

        if self.uri:
            db = Connection(self.uri)
            try:
                records = db.do(sql)
            finally:
                db.rollback()
                db.close()
            if records:
                fields = [x for x in records[0].keys()
                            if not x.startswith("__") and not x.endswith("__")]
        else:
            with self.env.db_query as db:
                cursor = db.cursor()
                records = cursor.execute(sql).fetchall()
                fields = get_column_names(cursor)

        if records:
            headers = [Header(f) for f in fields]
            groups = OrderedDict()
            for record in records:
                style = ""

                if "__color__" in record:
                    style += "background-color: %s" % record["__color__"]
                    record.remove("__color__")

                if "__group__" in record:
                    group = record["__group__"]
                    record.remove("__group__")
                    row = Row([Cell(v) for v in record], style=style)
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(row)
                else:
                    row = Row([Cell(v) for v in record], style=style)
                    if None not in groups:
                        groups[None] = []
                    groups[None].append(row)

            s = StringIO()
            for group, rows in groups.iteritems():
                t = Table(headers, rows, cls="wiki")
                t.refresh()
                if group:
                    s.write("=== %s ===\n" % group)
                s.write("{{{#!html\n")
                s.write(t.toHTML())
                s.write("\n}}}\n")

            v = s.getvalue()
            s.close()
            context = web_context(formatter.req)
            return format_to_html(self.env, context, v)
        else:
            return "No results"
