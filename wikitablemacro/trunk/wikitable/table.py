# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martin Aspeli <optilude@gmail.com>
# Copyright (C) 2012-2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import implements
from trac.db.api import get_column_names
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.formatter import format_to_html, system_message
from trac.wiki.macros import WikiMacroBase
from trac.util.text import exception_to_unicode, to_unicode
from trac.util.translation import _
from trac.util.html import html as tag

try:
    unicode = unicode
except NameError:
    unicode = str


class SQLTable(WikiMacroBase):
    """Draw a table from a SQL query in a wiki page.

    Examples:
    {{{
        {{{
        #!SQLTable
            SELECT count(id) as 'Number of Tickets'
            FROM ticket
        }}}
    }}}
    """

    implements(ITemplateProvider)

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('wikitable', resource_filename(__name__, 'htdocs'))]

    # IWikiMacroBase methods

    def expand_macro(self, formatter, name, content):
        def format(item):
            if item is None:
                return tag.em('(NULL)')
            if item is True:
                return 'TRUE'
            if item is False:
                return 'FALSE'
            if not isinstance(item, unicode):
                item = to_unicode(item)
            return format_to_html(self.env, formatter.context, item)

        try:
            with self.env.db_query as db:
                cursor = db.cursor()
                cursor.execute(content)
                rows = cursor.fetchall()
                cols = get_column_names(cursor)
        except self.env.db_exc.DatabaseError as e:
            return system_message(_("Invalid SQL"), exception_to_unicode(e))

        add_stylesheet(formatter.req, 'wikitable/css/wikitable.css')
        return tag.table(tag.thead(tag.tr(tag.th(c) for c in cols)),
                         tag.tbody(tag.tr((tag.td(format(c)) for c in row),
                                          class_='even' if idx % 2 else 'odd')
                                   for idx, row in enumerate(rows)),
                         class_='listing wikitable')
