# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Martin Aspeli <optilude@gmail.com>
# Copyright (C) 2012-2105 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.web.chrome import add_stylesheet
from trac.wiki.formatter import system_message
from trac.wiki.macros import WikiMacroBase
from trac.util.html import html as tag
from trac.util.text import exception_to_unicode
from trac.util.translation import _


class SQLScalar(WikiMacroBase):
    """Output a number from a scalar (1x1) SQL query.

    Examples:
    {{{
        {{{
        #!SQLScalar
            SELECT count(id) as 'Number of Tickets'
            FROM ticket
        }}}
    }}}
    """

    # IWikiMacroBase methods

    def expand_macro(self, formatter, name, content):
        try:
            rows = self.env.db_query(content)
        except self.env.db_exc.DatabaseError as e:
            return system_message(_("Invalid SQL"), exception_to_unicode(e))
        else:
            value = rows[0][0] if len(rows) else "(NULL)"

        add_stylesheet(formatter.req, 'wikitable/css/wikitable.css')
        return tag.span(value, class_='wikiscalar')
