from genshi import HTML
from genshi.builder import tag
from genshi.filters import Transformer
from pkg_resources import resource_filename  # @UnresolvedImport
from trac.config import Option
from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Table, Column
from trac.perm import IPermissionRequestor
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.translation import domain_functions
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
import locale
import re
import time
from decimal import Decimal
from symbol import except_clause



_, tag_, N_, add_domain = domain_functions('ticketbudgeting', '_', 'tag_', 'N_', 'add_domain')

""" budgeting table object \
see trac/db_default.py for samples and trac/db/schema.py for implementation of objects """
BUDGETING_TABLE = Table('budgeting', key=('ticket', 'position'))[
        Column('ticket', type='int'),
        Column('position', type='int'),
        Column('username'),
        Column('type'),
        Column('estimation', type='numeric(10,2)'),
        Column('cost', type='numeric(10,2)'),
        Column('status', type='int'),
        Column('comment')]

authorizedToModify = ['TICKET_MODIFY', 'TRAC_ADMIN', 'TICKET_BUDGETING_MODIFY']

_VALUE_NAMES = 'username,type,estimation,cost,status,comment'
_VALUE_NAMES_LIST = _VALUE_NAMES.split(',')


_CONFIG_SECTION = 'budgeting-plugin'
# these options won't be saved to trac.ini
Option(_CONFIG_SECTION, 'types',
    'Implementation|Documentation|Specification|Test',
    'Types of work, which could be selected in select-box.')

Option(_CONFIG_SECTION, 'default_type', '-1',
                "If the configured default-type is not available,"
                " select -1 ==> first element in type list will be selected")
Option(_CONFIG_SECTION, 'default_estimation', '0.0')
Option(_CONFIG_SECTION, 'default_cost', '0.0')
Option(_CONFIG_SECTION, 'default_status', '0')

Option(_CONFIG_SECTION, 'retrieve_users', 'permission',
    """indicates whether users should be retrieved from session or permission
    table; possible values: permission, session""")
Option(_CONFIG_SECTION, 'exclude_users',
   "'anonymous','authenticated','tracadmin'",
   """list of users, which should be excluded to show in the drop-down list; 
   should be usable as SQL-IN list""")

class Budget:
    """ Container class for budgeting info"""
    _action = None
    _values = None
    _pos = None
    _diff = None

    def __init__(self, values=None):
        self._values = {}
        if values:
            self._pos = values[0]
            for index, field in enumerate(_VALUE_NAMES_LIST):
                self.set(field, values[index + 1]);

    def set(self, field, value):
        if field in _VALUE_NAMES_LIST:
            if field == 'status':
                try:
                    self._values[field] = 0 if value == '' else int(value)
                except Exception, e:
                    raise Exception ('%s.%s' % (BUDGETING_TABLE.name, field), e)
            elif field in ('estimation', 'cost'):
                try:
                    try:
                        # read from request arguments
                        self._values[field] = (Decimal('0.00') if value == ''
                            else Decimal('%0.2f' % float(value.replace(',', '.'))))
                    except:
                        # loaded from DB
                        self._values[field] = Decimal(value)
                except Exception, e:
                    raise Exception ('%s.%s' % (BUDGETING_TABLE.name, field), e)
            else:
                self._values[field] = value

    def do_action(self, env, ticket_id):
        if not self._action:
            env.log.warn('no action defined!')
            return

        self._diff = {}

        if not ticket_id or not self._pos:
            env.log.error('no ticket-id or position available!')

        elif self._action == "insert":
            setAttrs = 'ticket,position'
            setValsSpace = '%s,%s'
            setVals = [ticket_id, self._pos]
            for key, value in self._values.iteritems():
                if key in ('username', 'type', 'comment'):
                    value = value.encode("utf-8")

                setAttrs += ",%s" % key
                setValsSpace += ",%s"
                setVals.append(value)

            self._diff[''] = (self._toStr(), '')

            sql = ("INSERT INTO %s (%s) VALUES (%s)" %
                    (BUDGETING_TABLE.name, setAttrs, setValsSpace))
            env.db_transaction(sql, setVals)
            env.log.error("Added Budgeting-row at positon %s to ticket %s:"
                          "\n%s" % (self._pos, ticket_id, self._toStr()))
            return

        elif self._action == "update":
            chFields = None
            for f in self._values.iterkeys():
                chFields = '%s, %s' % (chFields, f) if chFields else f

            oldVals = dict(zip(self._values.keys(),
                               env.db_query("SELECT %s FROM %s "
                                            "WHERE ticket=%%s AND position =%%s"
                                            % (chFields, BUDGETING_TABLE.name),
                                            (ticket_id, self._pos))[0]))

            changes = None
            newVals = []

            for key, value in self._values.iteritems():
                if not oldVals[key] == value:
                    new = '%s: %s' % (key, value)
                    old = '%s: %s' % (key, oldVals[key])

                    # value is not directly inserted to prevent sql-injection
                    newVals.append(str(value))
                    c = "%s=%%s" % key
                    changes = '%s, %s' % (changes, c) if changes else c
                    self._diff[".%s" % key] = (new, old)

            if changes:
                sql = ("UPDATE %s SET %s WHERE ticket=%s AND position=%s"
                        % (BUDGETING_TABLE.name, changes, ticket_id, self._pos))
                env.db_transaction(sql, newVals)
                env.log.error(sql)
                env.log.error("Updated Budgeting-row for ticket %s"
                              " at positon %s:\n%s" %
                              (ticket_id, self._pos, self._toStr()))
            return

        elif self._action == "delete":
            self._diff[''] = ('', self._toStr())

            sql = ("DELETE FROM %s WHERE ticket=%%s AND position=%%s"
                    % BUDGETING_TABLE.name)
            env.db_transaction(sql, (ticket_id, self._pos))

            env.log.debug("Deleted Budgeting-row for ticket %s"
                " at positon %s:\n%s" % (ticket_id, self._pos, self._toStr()))
            return

        env.log.error('no appropriate action found! _action is: %s' % self._action)

    def get_values(self):
        return self._values

    def _toStr (self):
        s = None
        for field in _VALUE_NAMES_LIST:
            f = '%s: %s' % (field, self.get(field))
            s = '%s, %s' % (s, f) if s else f
        return s

    def get(self, field):
        return self._values[field] if self._values.has_key(field) else None

    def getDiff(self):
        return self._diff

    def get_fieldset_row(self, view):
        users = tag.select(onchange='update("budgeting-%s-username")' % self._pos,
                           class_='budgeting_select',
                           name='budgeting-%s-username' % self._pos);
        user_in_list = False
        for u in view._budgeting_users_list:
            if self.get('username') == u:
                user_in_list = True
                users.append(tag.option(u, selected='selected'))
            else:
                users.append(tag.option(u))
        if not user_in_list:
            users.append(tag.option(self._values['username'],
                                    selected='selected'))

        types = tag.select(onchange='update("budgeting-%s-type")' % self._pos,
                           class_='budgeting_select',
                           name='budgeting-%s-type' % self._pos);
        type_in_list = False
        for t in view._types.split('|'):
            if self.get('type') == t:
                type_in_list = True
                types.append(tag.option(t, selected='selected'))
            else:
                types.append(tag.option(t))
            
        if not type_in_list:
            types.append(tag.option(self._values['type'], selected='selected'))

        return tag.tr(
          tag.td(users),
          tag.td(types),
          tag.td(tag.input(value=self._values['estimation'],
             onChange='update("budgeting-%s-estimation")' % self._pos,
             name='budgeting-%s-estimation' % self._pos, size='10')),
          tag.td(tag.input(value=self._values['cost'],
             onChange='update("budgeting-%s-cost")' % self._pos,
             name='budgeting-%s-cost' % self._pos, size='10')),
          tag.td(tag.input(value=self._values['status'],
             onChange='update("budgeting-%s-status")' % self._pos,
             name='budgeting-%s-status' % self._pos, size='10')),
          tag.td(tag.input(value=self._values['comment'],
             onChange='update("budgeting-%s-comment")' % self._pos,
             name='budgeting-%s-comment' % self._pos, size='60')),
          tag.td(tag.div(tag.input(value=u'\u2718', type='button',
             onclick='deleteRow(%s)' % self._pos, class_='deleteBudgetRow',
             name='deleteRow%s' % self._pos), class_='inlinebuttons')),
          id='budgeting-row-%s' % self._pos)

    def get_preview_row(self):
        row = tag.tr()
        for field in _VALUE_NAMES_LIST:
            row.append(tag.td('%s%s' % (self._values[field],
                              ' %' if field == 'status'  else'')))
        return row

"""
Main Api Module for Plugin ticketbudgeting
"""
class TicketBudgetingView(Component):
    implements(ITemplateProvider, IRequestFilter, ITemplateStreamFilter, ITicketManipulator)
    #  ITicketChangeListener

    _budgets = None
    _changed_by_author = None
    _budgeting_users_list = None
    _budgeting_users = None
    _types = None

    BUDGET_REPORT_ALL = (90, 'report_title_90', 'report_description_90',
    u"""SELECT t.id, t.summary, t.milestone AS __group__,
           '../milestone/' || t.milestone AS __grouplink__,
           t.owner, t.reporter, t.status, t.type, t.priority, t.component,
           COUNT(b.ticket) AS num,
           SUM(b.cost) AS cost,
           SUM(b.estimation) AS estimation,
           FLOOR(AVG(b.status)) || '%' AS status, 
           (CASE t.status 
               WHEN 'closed' THEN 'budgeting_report_closed'
               ELSE (CASE SUM(b.cost) > SUM(b.estimation)
                      WHEN true THEN 'budgeting_report_est_exceeded'
                    END)
           END) AS __class__
    FROM ticket t LEFT JOIN budgeting b ON b.ticket = t.id
    WHERE
        t.milestone LIKE (CASE $MILESTONE WHEN '' THEN '%' ELSE $MILESTONE END)
    AND
        (t.component LIKE (CASE $COMPONENT WHEN '' THEN '%' ELSE $COMPONENT END)
        OR t.component IS NULL)
    AND 
        (t.owner LIKE (CASE $OWNER WHEN '' THEN $USER ELSE $OWNER END)
        OR t.owner IS NULL OR b.username LIKE (CASE $OWNER 
                                                WHEN '' THEN $USER ELSE $OWNER
                                              END))
    GROUP BY
        t.id, t.type, t.priority, t.summary, t.owner, t.reporter,
        t.component, t.status, t.milestone
    HAVING COUNT(b.ticket) > 0
    ORDER BY t.milestone desc, t.status, t.id
    DESC""")

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    def filter_stream(self, req, method, filename, stream, data):
        """ overloaded from ITemplateStreamFilter """
        if self._check_init() == False:
            self.create_table()
            self.create_reports()
        if filename == 'ticket.html' and data:
            stream = self._insert_ticket_fields(data, stream, req)
        elif filename == 'milestone_view.html':
            by = 'component'
            if 'by' in req.args:
                by = req.args['by']
            budget_stats, stats_by = self._get_milestone_html(req, by)
            stats_by = "<fieldset><legend>Budget</legend><table>%s</table></fieldset>" % stats_by
            stream |= Transformer('//form[@id="stats"]').append(HTML(stats_by))
            stream |= Transformer('//div[@class="info"]').append(HTML(budget_stats))
        return stream

    def _insert_ticket_fields(self, data, stream, req):
        tkt = data['ticket']
        self._budgets = {}
        if tkt and tkt.id:
            self._load_budget(tkt.id)

            preview_rows = tag()
            if self._budgets:
                for budget in self._budgets:
                    preview_rows.append(budget.get_preview_row())
            stream |= (Transformer('//div [@id="content"]//div [@id="ticket"]')
                            .after(self._get_budget_preview(preview_rows)))

            modifyAllowed = False
            for authorizedPerm in authorizedToModify:
                modifyAllowed = modifyAllowed or authorizedPerm in req.perm(tkt.resource)
    
            if modifyAllowed:
                self._types = getBudgetConf(self, 'types')
                self.load_user_list()
                field_rows = tag()
                if self._budgets:
                    for budget in self._budgets:
                        field_rows.append(budget.get_fieldset_row(self))
                stream |= (Transformer('.//fieldset [@id="properties"]')
                           .after(self._get_budget_fieldset(req, field_rows)))
        return stream

    def _get_budget_fieldset(self, req, field_rows):

        row_adder = tag.div(tag.label(_('Add a new row')),
            tag.input(type="button", name="addRow", class_="addBudgetRow",
                      onclick="addBudgetRow()", value=u'\u271A'),
            class_="inlinebuttons")

        b_table = tag.table(
            tag.thead(tag.tr(
                tag.th(_('Person'), class_='budget_person'),
                tag.th(_('Type'), class_='budget_type'),
                tag.th(_('Estimation'), class_='budget_estimation',
                       title=_('in hours')),
                tag.th(_('Cost'), class_='budget_cost', title=_('in hours')),
                tag.th(_('State'), class_='budget_status'),
                tag.th(_('Comment'), class_='budget_comment'))),
            tag.tbody(field_rows if field_rows else '', id="budget_container"),
            id="budget_table")

        defaults = tag.div(
            tag.a(self._types, id="selectTypes"),
            tag.a(self._budgeting_users, id="selectNames"),
            tag.a(req.authname, id="def_name"),
            tag.a(getBudgetConf(self, 'default_type'), id="def_type"),
            tag.a(getBudgetConf(self, 'default_estimation'), id="def_estimation"),
            tag.a(getBudgetConf(self, 'default_cost'), id="def_cost"),
            tag.a(getBudgetConf(self, 'default_status'), id="def_status"),
            style="display: none")

        return tag.fieldset(
            tag.legend(_('Budget Estimation')),
            row_adder, b_table, defaults,
            id="budget")

    def _get_budget_preview(self, budgeting_rows):
        return tag.div(
            tag.h2(_('Budget Estimation'), class_="foldable"),
            tag.table(
                tag.thead(tag.tr(
                    tag.th(_('Person'), class_='budget_person'),
                    tag.th(_('Type'), class_='budget_type'),
                    tag.th(_('Estimation'), class_='budget_estimation'),
                    tag.th(_('Cost'), class_='budget_cost'),
                    tag.th(_('State'), class_='budget_status'),
                    tag.th(_('Comment')))),
               tag.tbody(budgeting_rows, id="preview_container"),
            class_="listing"), id='budgetpreview')

    def pre_process_request(self, req, handler):
        """ overridden from IRequestFilter"""
        return handler

    def post_process_request(self, req, template, data, content_type):
        """ overridden from IRequestFilter"""
        isReport = req.path_info.startswith('/report')
        isTicket = (req.path_info.startswith('/newticket') or
                    req.path_info.startswith('/ticket'))

        if  isReport or isTicket:
            add_stylesheet(req, 'hw/css/ticketbudgeting.css')

        if isTicket:
            add_script(req, 'hw/js/budgeting.js')
            if not data:
                return template, data, content_type
            tkt = data['ticket']

            if tkt and tkt.id and Ticket.id_is_valid(tkt.id):  # ticket is ready for saving
                if self._changed_by_author:
                    self._save_budget(tkt)
                self._budgets = None
        return template, data, content_type

    def _get_milestone_html(self, req, group_by):
        html = ''
        stats_by = ''
        ms = req.args['id']

        sql = "SELECT t.%s," % group_by if group_by else "SELECT"
        sql += (" SUM(b.cost), SUM(b.estimation), AVG(b.status)"
                " FROM budgeting b, ticket t"
                " WHERE b.ticket=t.id AND t.milestone='%s'" % ms)
        sql += (" GROUP BY t.%s ORDER BY t.%s" % (group_by, group_by))

        try:
            result = self.env.db_query(sql)
            if group_by:
                for row in result:
                    status_bar = self._get_progress_html(row[1], row[2], row[3], 75)
                    link = req.href.query({'milestone': ms, group_by: row[0]})
                    if group_by == 'component':
                        link = req.href.report(90, {'MILESTONE': ms, 'COMPONENT': row[0], 'OWNER': '%'})
    
                    stats_by += '<tr><th scope="row"><a href="%s">' \
                        '%s</a></th>' % (link, row[0])
                    stats_by += '<td>%s</td></tr>' % status_bar
            else:
                for row in result:
                    html = '<dl><dt>' + _('Budget in hours') + ':</dt><dd> </dd>' \
                            '<dt>' + _('Cost') + ': <dd>%.2f</dd></dt>' \
                            '<dt>' + _('Estimation') + ': <dd>%.2f</dd></dt>' \
                            '<dt>' + _('Status') + ': <dd>%.1f%%</dd></dt></dl>'
                    html = html % (row[0], row[1], row[2])
                    html = self._get_progress_html(row[0], row[1], row[2]) + html
        except Exception, e:
            self.log.error("Error executing SQL Statement \n %s" % e)

        return html, stats_by

    def _get_progress_html(self, cost, estimation, status, width=None):
        ratio = int (0)
        if estimation > 0 and cost:
            leftBarValue = int(round((cost * 100) / estimation, 0))
            ratio = leftBarValue
            rightBarValue = int(round(100 - leftBarValue, 0))
            if(rightBarValue + leftBarValue < 100):
                rightBarValue += 1
            elif leftBarValue > 100:
                leftBarValue = int(100)
                rightBarValue = int(0)
        else:
            leftBarValue = int(0)
            rightBarValue = int(100)

        style_cost = "width: " + str(leftBarValue) + "%"
        style_est = "width: " + str(rightBarValue) + "%"
        title = ' title="' + _('Cost') + ' / ' + _('Estimation') + ': %.1f / %.1f (%.0f %%); ' + _('Status') + ': %.1f%%"'
        title = title % (cost, estimation, ratio, status)
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
               </td></tr></table><p class="percent"' + title + '>' + right_legend + '</p>'

        return status_bar

    #===========================================================================
    # Loads all budgeting entries for given ticket-id from DB and stores them
    # into _self.budgets.
    #===========================================================================
    def _load_budget(self, ticket_id):
        self._budgets = []
        if not ticket_id:
            return
        sql = ("SELECT position, %s FROM budgeting WHERE ticket=%%s"
               " ORDER BY position" % _VALUE_NAMES)

        try:
            result = self.env.db_query(sql, (ticket_id,))
            for row in result:
                budget = Budget(row)
                self._budgets.append(budget)
                self.log.debug("[_load_budget] loaded budget: %s %s" %
                               (row[0], budget.get_values()))
        except Exception, e:
            self.log.error("Error executing SQL Statement %s \n Error: %s" %
                           (sql % ticket_id, e))

    #===========================================================================
    # Saves all added, changed and deleted budgeting entries from _self.budgets
    # to DB.
    #===========================================================================
    def _save_budget(self, tkt):
        if self._budgets and tkt and tkt.id:
            user = self._changed_by_author
            self._changed_by_author = None
            for pos, budget in self._budgets.iteritems():
                budget.do_action(self.env, tkt.id)
                self.log.debug("saved budget of position: %s" % pos)
            self._log_changes(tkt, user)
            self._budgets = None

    #===========================================================================
    # Logs changes in Budgeting to DB. (Changes are stored in budget._diff)
    #===========================================================================
    def _log_changes(self, tkt, change_user):
        if not tkt or not tkt.id:
            return
        cur_time = self._get_current_time()

        try:
            for pos, budget in self._budgets.iteritems():
                if budget.getDiff():
                    diff = budget.getDiff()
                    for key, (new, old) in diff.iteritems():
                        sql = ("INSERT INTO ticket_change "
                               "(ticket,time,author,field,oldvalue,newvalue) "
                               "VALUES(%s,%s,%s,%s,%s,%s)")
                        self.env.db_transaction(sql ,
                            (tkt.id, cur_time, change_user,
                             'budgeting.%s%s' % (pos, key), old, new))
        except Exception, ex:
            self.log.error("Error while logging change: %s" % ex)

    #===========================================================================
    # If a valid validation check was performed, the budgeting data will
    # be stored to database
    #===========================================================================
    def validate_ticket(self, req, ticket):
        """ overriden from ITicketManipulator """
        errors = []
        try:
            self._budgets = self._get_changed_budgets(req)
            for pos, b in self._budgets.iteritems():
                self.log.error(b._toStr)
            self._changed_by_author = req.authname or 'anonymous'
            self.log.info("[validate] budget has been changed by author: %s"
                           % self._changed_by_author)
        except Exception, ex:
            self.log.error("Error while validating: %s" % ex)
            field, e = ex
            errors.append([field, str(e)])
        return errors

    #===========================================================================
    # Get all Budgets that have been changed in the fieldset from req.args
    #===========================================================================
    def _get_changed_budgets(self, req):
        changedbudgets = {}
        budget = None
        for arg in req.args:
            # budgeting fields are named like budgeting-POS-FIELDNAME-ACTION
            field_attrs = arg.split("-")
            if len(field_attrs) == 4 and field_attrs[0] == 'budgeting':
                self.log.error('%s: %s' % (arg, req.args.get(arg)))
                pos = field_attrs[1]
                if changedbudgets.has_key(pos):
                    budget = changedbudgets[pos]
                else:
                    budget = Budget()
                    budget._pos = pos
                    if field_attrs[3] in ("insert", "delete", "update"):
                        budget._action = field_attrs[3]
                    changedbudgets[pos] = budget
                budget.set(field_attrs[2], req.args.get(arg))
        return changedbudgets

    def _check_init(self):
        """First setup or initentities deleted
            check initialization, like db setup etc."""
        if (self.config.get(_CONFIG_SECTION, 'version')):
            self.log.debug ("have local ini, so everything is set")
            return True
        else:
            self.log.debug ("check database")
            try:
                self.env.db_query("SELECT ticket FROM %s" %
                                  BUDGETING_TABLE.name)
                self.config.set(_CONFIG_SECTION, 'version', '1')
                self.config.save()
                self.log.info ("created local ini entries with name budgeting")
                return True
            except Exception:
                self.log.warn ("[_check_init] error while checking database;"
                               " table 'budgeting' is probably not present")

        return False

    def create_table(self):
        '''
        Constructor, see trac/postgres_backend.py:95 (method init_db)
        '''
        conn, dummyArgs = DatabaseManager(self.env).get_connector()
        try:
            with self.env.db_transaction as db:
                for stmt in conn.to_sql(BUDGETING_TABLE):
                    self.log.info("[INIT table] executing sql: %s" % stmt)
                    db(stmt)
                    self.log.info("[INIT table] successfully created table %s"
                                   % BUDGETING_TABLE.name)
        except Exception, e:
            self.log.error("[INIT table] Error executing SQL Statement \n %s" % e)

    def create_reports(self):
        report = self.BUDGET_REPORT_ALL
        try:
            sql = "SELECT id FROM report WHERE id=%s" % report[0]
            id = report[0]
            if not self.env.db_query(sql) == []:
                sql = "SELECT MAX(id) FROM report"
                id = self.env.db_query(sql)[0][0] + 1

            title = _(report[1])
            descr = _(report[2])
            descr = re.sub(r"'", "''", descr)
            query = _(report[3])
            self.log.info("descr: %s" % descr)
            self.log.info("query: %s" % query)
            self.log.info(" VALUES: %s, '%s', '%s'" % (id, title, query))
            sql = ("INSERT INTO report"
                   " (id, author, title, query, description) "
                   "VALUES"
                   " (%s, NULL, %s, %s, %s);")
            self.log.info("[INIT reports] executing sql: %s" % (sql % (id, title, query, descr)))
            self.env.db_transaction(sql, (id, title, query, descr))
            self.log.info("[INIT reports] successfully created report with id %s" % id)
        except Exception, e:
            self.log.info("[INIT reports] Error executing SQL Statement \n %s" % e)
            raise e

    def load_user_list(self):
        sql = ("SELECT DISTINCT session.sid FROM session")
        if self.config.get(_CONFIG_SECTION, 'retrieve_users') == "permission":
            sql += " JOIN permission ON session.sid = permission.username"
        sql += " WHERE authenticated > 0"
        excl_user = self.config.get(_CONFIG_SECTION, 'exclude_users')
        if excl_user and not excl_user == '':
            sql += " AND username NOT IN (%s)" % excl_user
        sql += " ORDER BY session.sid"
        try:
            result = self.env.db_transaction(sql)
            self._budgeting_users_list = []
            self._budgeting_users = None
            for row in result:
                self._budgeting_users_list.append(row[0])
                if self._budgeting_users:
                    self._budgeting_users += '|%s' % row[0]
                else:
                    self._budgeting_users = row[0]
            self.log.debug("INIT _budgeting_users: %s" % self._budgeting_users)
            self.log.debug("INIT _budgeting_users_list: %s" % self._budgeting_users_list)


        except Exception, e:
            self.log.error("Error executing SQL Statement %s\n %s" % (sql, e))

    def _get_current_time(self):
        return (time.time() - 1) * 1000000

    #===============================================================================
    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs
    #===============================================================================
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'htdocs')]

    def get_htdocs_dirs(self):
        return [('hw', resource_filename(__name__, 'htdocs'))]
#===========================================================================
# Class to publish an additional Permission Type
#===========================================================================
class TicketBudgetingPermission(Component):
    implements(IPermissionRequestor)
    """ publicise permission TICKET_BUDGETING_MODIFY """

    definedPermissions = ("TICKET_BUDGETING_MODIFY")
    # IPermissionRequestor
    def get_permission_actions(self):
        yield self.definedPermissions

def getBudgetConf(self, attr):
    return self.config.get(_CONFIG_SECTION, attr)
