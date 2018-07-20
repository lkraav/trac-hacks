# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2015 Franz Mayer Gefasoft AG
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import locale
import re
import time
from pkg_resources import resource_filename

from genshi import HTML
from genshi.filters import Transformer
from trac.config import Option, IntOption
from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Table, Column
from trac.perm import IPermissionRequestor
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util import exception_to_unicode
from trac.util.html import html
from trac.util.translation import domain_functions
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script

_, tag_, N_, add_domain = domain_functions('ticketbudgeting', '_',
                                           'tag_', 'N_', 'add_domain')

BUDGETING_TABLE = Table('budgeting', key=('ticket', 'position'))[
    Column('ticket', type='int'),
    Column('position', type='int'),
    Column('username'),
    Column('type'),
    Column('estimation', type='int64'),
    Column('cost', type='int64'),
    Column('status', type='int'),
    Column('comment')
]

BUDGET_REPORT_ALL_ID = 90

authorizedToModify = ['TICKET_MODIFY', 'TRAC_ADMIN',
                      'TICKET_BUDGETING_MODIFY']

_VALUE_NAMES = 'username,type,estimation,cost,status,comment'
_VALUE_NAMES_LIST = _VALUE_NAMES.split(',')


def get_float(value, fld='UNKNOWN FIELD'):
    try:
        if not value:
            ret_val = 0
        else:
            try:
                ret_val = locale.atof(value)
            except:
                str(value).replace(',', '.')
                ret_val = float(value)
    except Exception, e:
        fld = '%s.%s' % (BUDGETING_TABLE.name, fld)
        raise Exception(fld, e)
    return ret_val


class Budget:
    """ Container class for budgeting info"""
    _action = None
    _values = None
    _diff = None

    def __init__(self):
        self._values = {}

    def set(self, number, value):
        if number is None:
            return

        number = int(number)
        if 0 < number < len(_VALUE_NAMES_LIST) + 1:
            fld = _VALUE_NAMES_LIST[number - 1]

            if fld == 'status':
                try:
                    if value == '':
                        self._values[fld] = 0
                    else:
                        self._values[fld] = int(value)
                except Exception, e:
                    fld = '%s.%s' % (BUDGETING_TABLE.name, fld)
                    raise Exception(fld, e)
            elif fld in ('estimation', 'cost'):
                self._values[fld] = get_float(value, fld)
            else:
                self._values[fld] = value

    def do_action(self, env, ticket_id, position, def_cost=0):
        if not self._action:
            env.log.warn('no action defined!')
            return

        self._diff = {}

        if not ticket_id or not position:
            env.log.error('no ticket-id or position available!')

        elif self._action == "Insert":
            set_attrs = 'ticket,position'
            set_vals_space = '%s,%s'
            set_vals = [ticket_id, position]

            for key, value in self._values.iteritems():
                if key in ('username', 'type', 'comment'):
                    value = value.encode("utf-8")
                elif key == 'cost' and def_cost == -1:
                    value = 0

                set_attrs += ",%s" % key
                set_vals_space += ",%s"
                set_vals.append(value)

            self._diff[''] = (self._to_str(), '')
            sql = ("INSERT INTO %s (%s) VALUES (%s)" %
                   (BUDGETING_TABLE.name, set_attrs, set_vals_space))
            env.db_transaction(sql, set_vals)
            env.log.debug("Added Budgeting-row at position %s to ticket %s:"
                          "\n%s", position, ticket_id, self._to_str())

        elif self._action == "Update":

            old_values_sql = ("SELECT %s FROM %s WHERE"
                              " ticket=%%s AND position =%%s"
                              % (_VALUE_NAMES, BUDGETING_TABLE.name))
            old_values = env.db_query(old_values_sql,
                                      (ticket_id, position))[0]

            set_attrs = ''
            set_vals = []

            for attrnr in range(len(_VALUE_NAMES_LIST)):
                value = self.get_value(attrnr + 1)
                key = _VALUE_NAMES_LIST[attrnr]

                if key == 'cost' and def_cost == -1:
                    continue
                elif key in ('username', 'type', 'comment'):
                    value = value.encode("utf-8")
                elif key in ('estimation', 'cost', 'status'):
                    value = 0 if value == '' or get_float(value) == 0 \
                              else value

                if not old_values[attrnr] == value:
                    new = '%s: %s' % (key, value)
                    old = '%s: %s' % (key, old_values[attrnr])

                    if not set_attrs == '':
                        set_attrs += ','

                    set_attrs += '%s=%%s' % key
                    set_vals.append(str(value))

                    self._diff[".%s" % key] = (new, old)

            if not set_attrs == '':
                sql = ("UPDATE %s SET %s WHERE ticket=%%s AND position=%%s"
                       % (BUDGETING_TABLE.name, set_attrs))

                set_vals.append(ticket_id)
                set_vals.append(position)
                env.db_transaction(sql, set_vals)
                env.log.debug("Updated Budgeting-row for ticket %s"
                              " at position %s:\n%s",
                              ticket_id, position, self._to_str())

        elif self._action == "Delete":
            self._diff[''] = ('', self._to_str())

            sql = ("DELETE FROM %s WHERE ticket=%%s AND position=%%s"
                   % BUDGETING_TABLE.name)
            env.db_transaction(sql, (ticket_id, position))

            env.log.debug("Deleted Budgeting-row for ticket %s"
                          " at position %s:\n%s",
                          ticket_id, position, self._to_str())
        else:
            env.log.error('no appropriate action found! _action is: %s',
                          self._action)

    def get_values(self):
        return self._values

    def _to_str(self):
        return ("username: %s, type: %s, estimation: %s, cost: %s,"
                " state: %s, comment: %s" %
                (self.get_value(1), self.get_value(2), self.get_value(3),
                 self.get_value(4), self.get_value(5), self.get_value(6)))

    def get_value(self, number):
        if number is None:
            return ""

        number = int(number)
        if 0 < number < _VALUE_NAMES_LIST.__len__() + 1:
            fld = _VALUE_NAMES_LIST[number - 1]
            if fld in 'estimation':
                return locale.format('%.2f', self._values[fld])
            elif fld in 'cost':
                if 'cost' in self._values:
                    return locale.format('%.2f', self._values[fld])
                else:
                    return locale.format('%.2f', 0)
            return self._values[fld]
        return ""

    def set_action(self, action):
        self._action = action

    def get_diff(self):
        return self._diff


class TicketBudgetingView(Component):
    implements(ITicketManipulator, ITemplateProvider, ITemplateStreamFilter,
               IRequestFilter)

    _CONFIG_SECTION = 'budgeting-plugin'

    # these options won't be saved to trac.ini
    _types = Option(
        _CONFIG_SECTION, 'types',
        'Implementation|Documentation|Specification|Test',
        """Types of work, which could be selected in select-box.""")

    Option(
        _CONFIG_SECTION, 'retrieve_users', "permission",
        """indicates whether users should be retrieved from session or
        permission table; possible values: permission, session""")

    Option(
        _CONFIG_SECTION, 'exclude_users',
        "'anonymous','authenticated','tracadmin'",
        """list of users, which should be excluded to show in the
        drop-down list; should be usable as SQL-IN list""")

    _def_cost = IntOption(
        _CONFIG_SECTION, 'default_cost', 0,
        doc="""Default costs or -1 to disabled entering costs.
               This might useful when costs are entered by third
               party software.""")

    _type_list = None
    _name_list = None
    _name_list_str = None
    _budgets = None
    _changed_by_author = None

    BUDGET_REPORTS = [
        (BUDGET_REPORT_ALL_ID, 'report_title_90', 'report_description_90',
         """SELECT t.id, t.summary,
                   t.milestone AS __group__, '../milestone/' ||
                   t.milestone AS __grouplink__, t.owner, t.reporter,
                   t.status, t.type, t.priority, t.component,
                   COUNT(b.ticket) AS Count, SUM(b.cost) AS Cost,
                   SUM(b.estimation) AS Effort,
                   %(status)s || '%%' AS "Status",
          (CASE
            WHEN t.status='closed'
            THEN 'color: #777; background: #ddd; border-color: #ccc;'
            WHEN SUM(b.cost) > SUM(b.estimation)
            THEN 'font-weight: bold; background: orange;'
           END) AS __style__
         FROM ticket t
         LEFT JOIN budgeting b ON b.ticket = t.id
         WHERE t.milestone LIKE
         (CASE $MILESTONE
                   WHEN '' THEN '%%'
                   ELSE $MILESTONE END) and
         (t.component LIKE (CASE $COMPONENT
                   WHEN '' THEN '%%'
                   ELSE $COMPONENT END) or t.component is null) and
         (t.owner LIKE (CASE $OWNER
                   WHEN '''' THEN $USER
                   ELSE $OWNER END) or t.owner is null or
          b.username LIKE (CASE $OWNER
                   WHEN '''' THEN $USER
                   ELSE $OWNER END) )
         GROUP BY t.id, t.type, t.priority, t.summary, t.owner, t.reporter,
                  t.component, t.status, t.milestone
         HAVING COUNT(b.ticket) > 0
         ORDER BY t.milestone DESC, t.status, t.id DESC
         """)]

    def __init__(self):
        try:
            locale_dir = resource_filename(__name__, 'locale')
        except KeyError:
            pass
        else:
            add_domain(self.env.path, locale_dir)

        try:
            self.env.db_query("SELECT ticket FROM %s where ticket is null" %
                              BUDGETING_TABLE.name)
            self.log.debug("[TicketBudgetingView.__init__] table '%s' "
                           "already exists", BUDGETING_TABLE.name)
        except Exception:
            self.log.debug("[TicketBudgetingView.__init__] table '%s' "
                           "does not exists", BUDGETING_TABLE.name)
            try:
                self.create_table()
                self.log.info("[__init__] table '%s' successfully created",
                              BUDGETING_TABLE.name)
                self.create_reports()
                self.log.info("[__init__] report '%s' successfully created",
                              BUDGET_REPORT_ALL_ID)
            except Exception, e:
                self.log.error("[__init__] ERROR when creating table"
                               " or report: %s", e)

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' and data:
            tkt = data['ticket']
            if tkt and tkt.id:
                self._load_budget(tkt.id)
            else:
                self._budgets = {}

            input_html, preview_html = self._get_ticket_html()

            modify_allowed = False
            for perm in authorizedToModify:
                modify_allowed = modify_allowed or \
                                 perm in req.perm(tkt.resource)

            if modify_allowed:
                visibility = ' style="display: none"'
                if self._budgets:
                    visibility = ''

                fieldset = self._get_budget_fieldset() \
                           % (visibility, input_html)
                stream |= Transformer('.//fieldset [@id="properties"]')\
                          .after(HTML(fieldset))

                # Load default values for Type, Estimation, Cost an State
                # from trac.ini
                def_type = self._get_budget_attr('default_type')
                if not def_type:
                    # If the configured default-type is not available,
                    # submit -1 ==> first element in type list will be
                    # selected
                    def_type = '-1'
                def_est = self._get_budget_attr('default_estimation')
                if not def_est:
                    def_est = '0.0'

                def_state = self._get_budget_attr('default_state')
                if not def_state:
                    def_state = '0'

                defaults = html.div(
                    html.a(self._type_list, id="selectTypes"),
                    html.a(self._name_list_str, id="selectNames"),
                    html.a(req.authname, id="def_name"),
                    html.a(def_type, id="def_type"),
                    html.a(def_est, id="def_est"),
                    html.a(self._def_cost, id="def_cost"),
                    html.a(def_state, id="def_state"),
                    style="display: none")

                stream |= Transformer('.//fieldset [@id="budget"]')\
                          .append(defaults)

            if preview_html:
                fieldset_str = self._get_budget_preview() % preview_html
                stream |= Transformer('//div [@id="content"]'
                                      '//div [@id="ticket"]')\
                          .after(HTML(fieldset_str))
        elif filename == 'milestone_view.html':
            by = 'component'
            if 'by' in req.args:
                by = req.args['by']
            budget_stats, stats_by = self._get_milestone_html(req, by)
            stats_by = u"<fieldset><legend>Budget</legend>" \
                       u"<table>%s</table></fieldset>" % stats_by
            stream |= Transformer('//form[@id="stats"]')\
                      .append(HTML(stats_by))
            stream |= Transformer('//div[@class="info"]')\
                      .append(HTML(budget_stats))
        return stream

    def _get_budget_attr(self, name):
        return self.config.get('budgeting-plugin', name)

    def _get_budget_fieldset(self):
        title = _('in hours')
        fieldset = ('<fieldset id="budget">'
                    '<legend>' + _('Budget Estimation') + '</legend>'
                    '<div class="inlinebuttons">'
                    '<label>' + _('Add a new row') + '</label>'
                    '<input type="button" name="addRow" style="margin-left: 5px; border-radius: 1em 1em 1em 1em; font-size: 100%%" onclick="addBudgetRow()" value = "&#x271A;"/>'
                    '</div>'
                       '<span id="hiddenbudgettable"%s>'
                       '<table>'
                       '<thead id="budgethead">'
                       '<tr>'
                            '<th>' + _('Person') + '</th>'
                            '<th>' + _('Type') + '</th>'
                            '<th title="' + title + '">' + _('Estimation') + '</th>' +
                            ('<th title="' + title + '">' + _('Cost') + '</th>' if self._def_cost != -1 else '') +
                            '<th>' + _('State') + '</th>'
                            '<th style="width:300px">' + _('Comment') + '</th>'
                        '</tr>'
                        '</thead>'
                        '<tbody id="budget_container">%s</tbody>'
                        '</table>'
                        '</span>'
                        '</fieldset>')
        self.log.debug('fieldset: %s', fieldset)
        return fieldset

    def _get_budget_preview(self):
        fieldset = (
            '<div id="budgetpreview">'
            '<h2 class="foldable">' + _('Budget Estimation') + '</h2>'
            '<table class="listing">'
            '<thead>'
              '<tr>'
                '<th style="width:90px">' + _('Person') + '</th>'
                '<th style="width:90px">' + _('Type') + '</th>'
                '<th style="width:90px">' + _('Estimation') + '</th>'
                '<th style="width:90px">' + _('Cost') + '</th>'
                '<th style="width:90px">' + _('State') + '</th>'
                '<th style="width:300px">' + _('Comment') + '</th>'
              '</tr>'
            '</thead>'
            '<tbody id="previewContainer">%s'
            '</tbody>'
            '</table>'
            '</div>')
        return fieldset

    def pre_process_request(self, req, handler):
        """ overridden from IRequestFilter"""
        return handler

    def post_process_request(self, req, template, data, content_type):
        """ overridden from IRequestFilter"""
        if req.path_info.startswith('/newticket') or \
                req.path_info.startswith('/ticket'):
            add_script(req, 'hw/js/budgeting.js')
            if not data:
                return template, data, content_type
            tkt = data['ticket']

            if tkt and tkt.id and Ticket.id_is_valid(tkt.id):
                # ticket is ready for saving
                if self._changed_by_author:
                    self._save_budget(tkt)
                self._budgets = None
        return template, data, content_type

    def _get_fields(self, req):
        budget_dict = {}
        # searching budget fields and send them to db
        for arg in req.args:
            field_attrs = arg.split("-")
            if len(field_attrs) >= 2:
                row_no = field_attrs[0]
                if row_no in budget_dict:
                    budget_obj = budget_dict[row_no]
                else:
                    budget_obj = Budget()
                    budget_dict[row_no] = budget_obj
                budget_obj.set(field_attrs[1], req.args.get(arg))

                if len(field_attrs) == 3:
                    # New created field, should be insered
                    if field_attrs[2] in ('Insert', 'Delete', 'Update'):
                        budget_obj.set_action(field_attrs[2])
        return budget_dict

    def _get_milestone_html(self, req, group_by):
        html = ''
        stats_by = ''
        ms = req.args['id']

        for row in self.env.db_query("""
                SELECT SUM(b.cost), SUM(b.estimation), AVG(b.status)
                FROM budgeting b, ticket t
                WHERE b.ticket=t.id AND t.milestone=%s
                """, (ms,)):
            html = '<dl><dt>' + _('Budget in hours') + ':</dt><dd> </dd>' \
                   '<dt>' + _('Cost') + ': <dd>%.2f</dd></dt>' \
                   '<dt>' + _('Estimation') + ': <dd>%.2f</dd></dt>' \
                   '<dt>' + _('Status') + ': <dd>%.1f%%</dd></dt></dl>'
            html %= row[0], row[1], row[2]
            html = self._get_progress_html(row[0], row[1], row[2]) + html

        if not group_by:
            return html, stats_by

        for row in self.env.db_query("""
                SELECT t.%s, SUM(b.cost), SUM(b.estimation), AVG(b.status)
                FROM budgeting b, ticket t
                WHERE b.ticket=t.id AND t.milestone=%%s
                GROUP BY t.%s ORDER BY t.%s
                """ % (group_by, group_by, group_by), (ms,)):
            status_bar = self._get_progress_html(row[1], row[2], row[3], 75)
            link = req.href.query({'milestone': ms, group_by: row[0]})
            if group_by == 'component':
                link = req.href.report(BUDGET_REPORT_ALL_ID,
                                       {'MILESTONE': ms,
                                        'COMPONENT': row[0],
                                        'OWNER': '%'})

            stats_by += '<tr><th scope="row"><a href="%s">' \
                        '%s</a></th>' % (link, row[0])
            stats_by += '<td>%s</td></tr>' % status_bar

        return html, stats_by

    def _get_progress_html(self, cost, estimation, status, width=None):
        ratio = 0
        if estimation > 0 and cost:
            left_bar_value = int(round((cost * 100) / estimation, 0))
            ratio = left_bar_value
            right_bar_value = int(round(100 - left_bar_value, 0))
            if right_bar_value + left_bar_value < 100:
                right_bar_value += 1
            elif left_bar_value > 100:
                left_bar_value = int(100)
                right_bar_value = int(0)
        else:
            left_bar_value = int(0)
            right_bar_value = int(100)

        style_cost = "width: " + str(left_bar_value) + "%"
        style_est = "width: " + str(right_bar_value) + "%"
        title = ' title="' + _('Cost') + ' / ' + _('Estimation') + \
                ': %.1f / %.1f (%.0f %%); ' + _('Status') + ': %.1f%%"'
        title %= cost, estimation, ratio, status
        right_legend = "%.0f %%" % ratio

        if int(status) == 100:
            style_cost += ";background:none repeat scroll 0 0 #3300FF;"
            style_est += ";background:none repeat scroll 0 0 #00BB00;"
        elif ratio > 100:
            style_cost += ";background:none repeat scroll 0 0 #BB0000;"

        status_bar = '<table class="progress"'
        if width:
            status_bar += ' style="width: ' + str(width) + '%"'
            right_legend = "%.0f / %.0f" % (cost, estimation)
        status_bar += '><tr><td class="closed" style="' + style_cost + '">\
               <a' + title + '></a> \
               </td><td style="' + style_est + '" class="open">\
               <a' + title + '></a> \
               </td></tr></table><p class="percent"' + title + '>' + \
               right_legend + '</p>'

        return status_bar

    def _get_ticket_html(self):
        input_html = ''
        preview_html = ''

        if not self._type_list:
            types_str = self.config.get(self._CONFIG_SECTION, 'types')
            self._type_list = re.sub(r'\|', ';', types_str)
            self.log.debug("INIT self._type_list: %s", self._type_list)
        types = self._type_list.split(';')

        if not self._name_list:
            self._name_list = self.get_user_list()
            self.log.debug("INIT self._name_list: %s", self._name_list)
            for user in self._name_list:
                if not self._name_list_str:
                    self._name_list_str = str(user)
                else:
                    self._name_list_str += ';' + str(user)

        if self._budgets:
            for pos, budget in self._budgets.iteritems():
                user_options = ''
                type_options = ''
                values = budget.get_values()
                input_html += '<tr id="row-%s">' % pos
                preview_html += '<tr>'
                el_in_list = False

                if self._name_list:
                    for opt in self._name_list:
                        selected = ''
                        if values['username'] == opt:
                            selected = ' selected'
                            el_in_list = True
#                            preview_html += '<td>%s</td>' % opt
                        user_options += '<option%s>%s</option>' \
                                        % (selected, opt)
                if not el_in_list:
                    user_options += '<option selected>%s</option>' \
                                    % (values['username'])

                el_in_list = False
                for t in types:
                    selected = ''
                    if values['type'] == t:
                        selected = ' selected'
                        el_in_list = True
#                        preview_html += '<td>%s</td>' % t
                    type_options += '<option%s>%s</option>' % (selected, t)
                if not el_in_list:
                    type_options += '<option selected>%s</option>' \
                                    % (values['type'])

                input_html += '<td><select onChange="update(%s,1)" ' \
                              'name="%s-1" >%s</select></td>' \
                              % (pos, pos, user_options)
                preview_html += '<td>%s</td>' % values['username']
                input_html += '<td><select onChange="update(%s,2)" ' \
                              'name="%s-2">%s</select></td>' \
                              % (pos, pos, type_options)
                preview_html += '<td>%s</td>' % values['type']
                size = 10
                for col in range(3, 7):
                    col_val = budget.get_value(col)
                    if col == 6 and col_val:  # comment
                        col_val = col_val.replace('"', "&quot;")
                        size = 60
                    elif not col_val:
                        if col < 6:
                            col_val = '0'
                        else:
                            col_val = ''
                            size = 60

                    if col == 4 and self._def_cost == -1:  # disable cost
                        input_html += '<input type="hidden" name="%s-%s" value="%s" />' % (pos, col, 0)
                    else:
                        input_html += '<td><input size="%s" onChange="update(%s,%s)" name="%s-%s" value="%s"></td>' % (size, pos, col, pos, col, col_val)
                    preview_html += '<td>%s' % col_val
                    if col == 5:
                        preview_html += '&nbsp;%'
                    preview_html += '</td>'
                input_html += '<td><div class="inlinebuttons"><input type="button" style="border-radius: 1em 1em 1em 1em; font-size: 100%%" name="deleteRow%s" onclick="deleteRow(%s)" value = "&#x2718;"/></div></td>' % (pos, pos)
                input_html += '</tr>'
                preview_html += '</tr>'
        return input_html, preview_html

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'htdocs')]

    def get_htdocs_dirs(self):
        return [('hw', resource_filename(__name__, 'htdocs'))]

    def _load_budget(self, ticket_id):
        self._budgets = {}
        if not ticket_id:
            return

        for row in self.env.db_query("""
                SELECT position,username,type,estimation,cost,status,comment
                FROM budgeting WHERE ticket=%s ORDER BY position
                """, (ticket_id,)):
            budget = Budget()
            for i, col in enumerate(row):
                if i > 0:
                    budget.set(i, col)
            pos = int(row[0])
            self._budgets[pos] = budget
            self.log.debug("[_load_budget] loaded budget: %s",
                           budget.get_values())

    def _save_budget(self, tkt):
        if self._budgets and tkt and tkt.id:
            user = self._changed_by_author
            self._changed_by_author = None
            for pos, budget in self._budgets.iteritems():
                budget.do_action(self.env, tkt.id, int(pos), self._def_cost)
                self.log.debug("saved budget of position: %s", pos)
            self._log_changes(tkt, user)
            self._budgets = None

    def _log_changes(self, tkt, change_user):
        if not tkt or not tkt.id:
            return
        cur_time = self._get_current_time()

        try:
            for pos, budget in self._budgets.iteritems():
                if budget.get_diff():
                    diff = budget.get_diff()
                    for key, (new, old) in diff.iteritems():
                        sql = ("INSERT INTO ticket_change "
                               "(ticket,time,author,field,oldvalue,newvalue) "
                               "VALUES(%s,%s,%s,%s,%s,%s)")
                        self.env.db_transaction(sql,
                            (tkt.id, cur_time, change_user, 'budgeting.%s%s'
                             % (pos, key), old, new))
        except Exception, ex:
            self.log.error("Error while logging change: %s", ex)

    def _get_current_time(self):
        return (time.time() - 1) * 1000000

    def validate_ticket(self, req, ticket):
        """ overriden from ITicketManipulator """
        errors = []
        try:
            self._budgets = self._get_fields(req)
            self._changed_by_author = req.authname or 'anonymous'
            self.log.info("[validate] budget has changed by author: %s",
                           self._changed_by_author)
        except Exception, ex:
            self.log.error("Error while validating: %s", ex)
            fld, e = ex
            errors.append([fld, str(e)])

        return errors

    def create_table(self):
        """Constructor, see trac/postgres_backend.py:95 (method init_db)
        """
        conn, dummy_args = DatabaseManager(self.env).get_connector()
        try:
            with self.env.db_transaction as db:
                for stmt in conn.to_sql(BUDGETING_TABLE):
                    try:
                        if db.schema:
                            stmt = re.sub(r'CREATE TABLE ', 'CREATE TABLE "'
                                          + db.schema + '".', stmt)
                    except Exception, e:
                        self.log.warn("[INIT table] substituting schema "
                                      "throws error: %s", e)
                    stmt = re.sub(r'(?i)bigint', 'NUMERIC(10,2)', stmt)
                    self.log.info("[INIT table] executing sql: %s", stmt)
                    db(stmt)
                    self.log.info("[INIT table] successfully created "
                                  "table %s", BUDGETING_TABLE.name)
        except Exception, e:
            self.log.error("[INIT table] Error executing SQL Statement\n"
                           "%s", e)

    def create_reports(self):
        for report in self.BUDGET_REPORTS:
            sql = """
                INSERT INTO report (id, author, title, query, description)
                VALUES (%s, NULL, %s, %s, %s)
            """
            try:
                with self.env.db_transaction as db:
                    query = report[3] \
                            % {'status': db.cast('AVG(b.status)', 'int')}
                    db(sql, (report[0], _(report[1]), query, _(report[2])))
            except Exception, e:
                self.log.error("[INIT reports] Error executing SQL "
                               "Statement%s",
                               exception_to_unicode(e, traceback=True))
            else:
                self.log.info("[INIT reports] successfully created report "
                              "with id %s", report[0])

    def get_col_list(self, ignore_cols=None):
        """ return col list as string; usable for selecting all cols
        from budgeting table """
        col_list = ""
        i = 0
        for col in BUDGETING_TABLE.columns:
            try:
                if ignore_cols and ignore_cols.index(col.name) > -1:
                    continue
            except:
                pass

            if i > 0:
                col_list += ","
            col_list += col.name
            i += 1
        return col_list

    def get_user_list(self):
        sql_result = []

        sql = ("SELECT DISTINCT sid FROM session WHERE authenticated > 0"
               " ORDER BY sid")

        if self.config.get(self._CONFIG_SECTION, 'retrieve_users') == \
                'permission':
            sql = "SELECT DISTINCT username FROM permission"
            if self.config.get(self._CONFIG_SECTION, 'exclude_users'):
                excl_user = self.config.get(self._CONFIG_SECTION,
                                            'exclude_users')
                sql = "%s WHERE username NOT IN (%s)" % (sql, excl_user)
            sql += " ORDER BY username"
        for row in self.env.db_query(sql):
            sql_result.append(row[0])
        return sql_result


class TicketBudgetingPermission(Component):
    """Publicise permission TICKET_BUDGETING_MODIFY """
    implements(IPermissionRequestor)

    definedPermissions = "TICKET_BUDGETING_MODIFY"

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield self.definedPermissions
