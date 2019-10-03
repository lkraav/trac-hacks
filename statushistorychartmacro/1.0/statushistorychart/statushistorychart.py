#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013, 2015, 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import copy
from datetime import datetime
import re

from trac.util.html import tag
from pkg_resources import ResourceManager
from trac.core import Component, implements, TracError
from trac.ticket.api import TicketSystem
from trac.ticket.query import Query
from trac.util import datefmt
from trac.util.translation import _
from trac.web.chrome import add_script, ITemplateProvider, add_script_data
from trac.wiki.api import IWikiMacroProvider

re_param = re.compile("\$[a-zA-Z]+")


class Macro(Component):
    """ Provides [StatusHistoryChart] Macro. """

    implements(IWikiMacroProvider, ITemplateProvider)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('statushistorychart', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IWikiMacroProvider methods
    def get_macros(self):
        return ['StatusHistoryChart']

    def get_macro_description(self, name):
        return """Plot a graph of ticket's field change history.
 without arguments::
  If argument is omitted, use following:
  - Result for report or query, if used on report description.
  - Bound for milestone, if used on milestone description.
  - Your last query result. You're Feeling Lucky!
 args::
  - If you want to add filter, use TracQuery#QueryLanguage.
 Yaxis options::
   - Use '''{{{report}}}''' parameter in query for field name to plot.[[BR]]
  default: {{{status}}}
  - Use '''{{{format}}}''' parameter in query for yaxis values.[[BR]]
  slash {{{/}}} separated column name or {{{*}}} for wildcard.[[BR]]
  two or more value can join with '+' in one, rename with ' AS ' i.e. {{{/new/assigned+accepted AS in progress/closed}}}[[BR]]
  default: options for the field, i.e. {{{new/assigned/accepted/closed/*}}} for status.

 Example::
   {{{
   [[StatusHistoryChart]]
   [[StatusHistoryChart(format=new/*/closed)]]
   [[StatusHistoryChart(format=new/accepted+assigned AS in progress/closed)]]
   [[StatusHistoryChart(owner=$USER&format=new/*/closed)]]
   [[StatusHistoryChart(type=$TYPE&format=new/*/closed)]]  (uses CGI parameter for $TYPE)
   [[StatusHistoryChart(report=milestone)]]
   [[StatusHistoryChart(report=owner&format=/somebody/*/matobaa/)]]
   }}}"""

    def expand_macro(self, formatter, name, content, args=None):
        # Utility methods
        def lte_ie8(req):
            user_agent = formatter.req.get_header('user-agent')
            msie = user_agent.find('MSIE ')
            return (msie != -1) and user_agent[msie + 5:msie + 6] in ['6', '7', '8']

        def after_AS(string):
            index = string.find(' AS ')
            return index > 0 and string[index + 4:] or string

        def before_AS(string):
            index = string.find(' AS ')
            return index > 0 and string[:index] or string
        # add scripts
        if lte_ie8(formatter.req):
            add_script(formatter.req, "statushistorychart/js/flot/excanvas.js")
        add_script(formatter.req, "statushistorychart/js/flot/jquery.flot.js")
        add_script(formatter.req, "statushistorychart/js/flot/jquery.flot.time.js")
        add_script(formatter.req, "statushistorychart/js/enabler.js")
        # from macro parameters
        query = None
        query_href = None
        status_list = ['new', 'assigned', 'accepted', 'closed']  # default
        if(content):
            # replace parameters
            for match in reversed([match for match in re_param.finditer(content)]):
                param_name = match.group(0)
                if param_name == '$USER':
                    authname = formatter.req.authname
                    if authname == 'anonymous':
                        authname = 'anonymous||somebody'
                    content = content.replace(param_name, authname)
                else:
                    param_value = formatter.req.args.get(param_name[1:])
                    if param_value:
                        content = content.replace(param_name, param_value)
            # execute query
            query = Query.from_string(formatter.env, content)
        field = query and query.id or 'status'  # stopgap implementation; I use 'report' for y-axis parameter
        field = filter(lambda x: x['name'] == field, TicketSystem(self.env).fields)
        if len(field) <= 0:
            return tag.div(tag.strong('Error: Macro %s failed' % name),
                       tag.pre("%s is not field name" % query.id), class_="system-message")
        field = field[0]
        custom = 'custom' in field and field['custom'] or None
        status_list = query and query.format and query.format.split('/') or \
                      'options' in field and copy.copy(field['options']) or status_list
        if field['name'] == 'status' and not (query and query.format):
            def isprime(item):
                primaries = ['new', 'assigned', 'accepted', 'closed']
                return (item in primaries and [primaries.index(item)] or [len(primaries)])[0]
            status_list.sort(key=isprime)
        if '*' not in status_list:
            status_list.append('*')
        default_status = status_list.index('*')
        # execute query for ids of ticket
        if(query and len(query.constraint_cols) > 0):
            result = query.execute() or [{'id':-1}]  # Sentinel for no result
            cond = "ticket.id in (%s)" % ', '.join([str(t['id']) for t in result])
        elif formatter.resource.realm == 'milestone':
            cond = "ticket.milestone='%s'" % formatter.resource.id
        elif('query_tickets' in formatter.req.session):  # You Feeling Lucky
            query_tickets = formatter.req.session.get('query_tickets', '')
            query_href = formatter.req.session.get('query_href', '')
            tickets = len(query_tickets) and query_tickets.split(' ') or ['-1']  # Sentinel for no result
            cond = "ticket.id in (%s)" % ', '.join(tickets)
        else:
            raise TracError("%sMacro: Empty. There are no content and no context." % name)
        
        # count that how many appear this macro in a page
        callcount = formatter.req.__dict__.get('statushistorychart_count', None)
        if(callcount):
            callcount += 1
            formatter.req.statushistorychart_count = callcount
        else:
            callcount = 1
            formatter.req.__setattr__('statushistorychart_count', callcount)
        
        # execute query for value changes of each ticket
        join_clause_dummy = ''
        join_clause = "JOIN ticket_custom ON ticket.id = ticket_custom.ticket and ticket_custom.name = '%s'"
        fetchall = self.env.db_query("""
                SELECT id, time, null, %s, 'content'
                    FROM ticket
                    %s
                    WHERE %s
                UNION
                SELECT id, ticket_change.time, ticket_change.oldvalue, ticket_change.newvalue, "comment:" || comment.oldvalue
                    FROM ticket
                    JOIN ticket_change ON ticket.id = ticket_change.ticket
                    JOIN ticket_change comment on ticket_change.time = comment.time
                    WHERE %s AND ticket_change.field='%s' AND comment.field = 'comment'
                ORDER BY id, ticket_change.time
                """ % (custom and "'\uFEFF'" or field['name'],  # ZERO WIDTH NO-BREAK SPACE; uses for mark of invalid data
                       custom and (join_clause % field['name']) or join_clause_dummy,
                       cond, cond, field['name']))
        changes = [row for row in fetchall]
        # transform (ticket, time, status)* ==> (ticket <>- status)*
        tid = 0  # position of ticket id
        tickets = {}
        for change in changes:
            ticket = tickets.get(change[tid])  # slot is exist, or
            if ticket is None:
                ticket = tickets[change[tid]] = []  # create new slot and use it
            ticket.append(list(change))
        # generate status_list splitted, {a, b+c, d} => {a:0, b+c:1, b:1, c:1, d:2}
        status_list_splitted = {}
        for index, status in enumerate(map(before_AS, status_list)):
            status_list_splitted[status] = index
            if status.find('+') >= 0:
                for each in status.split('+'):
                    status_list_splitted[each] = index
#        groupstats = self.compmgr[DefaultTicketGroupStatsProvider]
#        ticket_groups = groupstats._get_ticket_groups()
#        for group in ticket_groups:
#            pass
        for tid in tickets:
            if len(tickets[tid]) > 1:
                tickets[tid][0][3] = tickets[tid][1][2]  # override last value with initial value
        # generate data
        data = []
        # points
        too_many_tickets = len(tickets) > 200
        for no, tid in enumerate(sorted(tickets)):
            if not too_many_tickets or tickets[tid][-1][3] != 'closed':
                void, time, void, state, hashes = tickets[tid][-1]  # @UnusedVariable
                # offset by req.tz
                time = datefmt.to_timestamp(datetime.fromtimestamp(time/1000000, formatter.req.tz).replace(tzinfo=datefmt.utc)) * 1000
                index = status_list_splitted.get(state, default_status)
                data.append({'points': {'show': True, 'radius': 8, 'color': no},
                             'label': tid,
                             'data': [[time, index, hashes]]})
        # lines
        for no, tid in enumerate(sorted(tickets)):
            data.append({'color': no, 'label': tid,
                         'data': [[datefmt.to_timestamp(datetime.fromtimestamp(time/1000000, formatter.req.tz).replace(tzinfo=datefmt.utc)) * 1000,
                                   status_list_splitted.get(state, default_status), hashes]
                                  for void, time, void, state, hashes in tickets[tid]]})  # @UnusedVariable
        from trac import __version__ as VERSION
        if VERSION[0:1] != '0':
        # render for trac 1.0 or later
            add_script_data(formatter.req, {('statushistorychart%s_yaxis' % callcount): map(after_AS, status_list)})
            add_script_data(formatter.req, {('statushistorychart%s_data' % callcount): data})
            return tag.div(class_="statushistorychart", id="statushistorychart%s" % callcount, style="width: 800px; height: 400px;")
        else:  # if trac < 1.0 or earlier
            from trac.util.presentation import to_json
            return tag.script("var statushistorychart%s_yaxis = %s; var statushistorychart%s_data = %s" \
                              % (callcount, to_json(map(after_AS, status_list)), callcount, to_json(data)),
                              type="text/javascript") \
                 + tag.div(class_="statushistorychart", id="statushistorychart%s" % callcount, style="width: 800px; height: 400px;")
