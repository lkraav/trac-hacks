# Copyright (C) 2009, 2011, 2013 John Szakmeister
# Copyright (C) 2016 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file LICENSE.txt, which
# you should have received as part of this distribution.

import re
import json as simplejson
from collections import defaultdict
from operator import itemgetter
from pkg_resources import get_distribution, parse_version
from genshi.template.markup import MarkupTemplate
from genshi.builder import tag
from trac.core import *
from trac.db import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.ticket.api import ITicketChangeListener, TicketSystem
from trac.ticket.model import Ticket, Milestone
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_ctxtnav, add_script, add_script_data, add_stylesheet, Chrome, ResourceNotFound
from trac.web.main import IRequestHandler
from trac.web.api import HTTPBadRequest, IRequestFilter
from trac.util.datefmt import format_date
from trac.util.html import html
from trac.util import get_reporter_id
from trac.util.text import _, unicode_quote, unicode_from_base64, unicode_to_base64

from multiprojectbacklog.schema import schema_version, schema
try:
    from simplemultiproject.model import SmpModel
    have_smp = True
except ImportError:
    have_smp = False

class MultiProjectBacklog(Component):
    implements(INavigationContributor, IRequestHandler, IRequestFilter,
               IEnvironmentSetupParticipant, ITemplateProvider,
               ITicketChangeListener, IPermissionRequestor)

    _ticket_fields = [ 
        u'id', u'summary', u'component', u'version', u'type', u'owner', u'status',
        u'time_created'
    ]
    _ticket_fields_sel = [
        (u'id', u'Id'), (u'summary', u'Summary'), (u'component', u'Component'),
        (u'version', u'Version'), (u'type', u'Type'), (u'owner', u'Owner'),
        (u'status', u'Status'), (u'time_created', u'Created')
    ]

    trac_version = get_distribution('trac').version
    trac_0_12 = parse_version(trac_version) < parse_version('1.0.0')  # True if Trac V0.12.x

    def __init__(self):
        if have_smp:
            self.__SmpModel = SmpModel(self.env)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        connector, args = DatabaseManager(self.env)._get_connector()
        to_sql = connector.to_sql
        db = self.env.get_db_cnx()
        cur = db.cursor()

        for table in schema:
            sql = to_sql(table)
            for stmt in sql:
                cur.execute(stmt)

        # Insert version information
        cur.execute("INSERT INTO system (name,value) "
                    "VALUES ('mp_backlog_version', %s)" % (
                        str(schema_version)))

    def environment_needs_upgrade(self, db):
        cur = db.cursor()
        cur.execute("SELECT value FROM system WHERE name='mp_backlog_version'")
        row = cur.fetchone()
        if not row or int(row[0]) < schema_version:
            return True

        cur.execute("SELECT COUNT(*) FROM mp_backlog "
                    "LEFT JOIN ticket ON ticket.id = mp_backlog.ticket_id "
                    "WHERE ticket.id IS NULL")
        num_ranks_without_tickets = cur.fetchone()[0]
        if num_ranks_without_tickets:
            return True

        cur.execute("SELECT COUNT(*) FROM ticket AS t LEFT JOIN mp_backlog "
                    "ON t.id = mp_backlog.ticket_id WHERE mp_backlog.ticket_id "
                    "IS NULL")

        num_tickets_without_ranks = cur.fetchone()[0]

        if num_tickets_without_ranks:
            return True

        return False

    def upgrade_environment(self, db):
        cur = db.cursor()
        cur.execute(
                "SELECT value FROM system WHERE name='mp_backlog_version'")
        row = cur.fetchone()

        if not row:
            self.environment_created()
        elif int(row[0]) < schema_version:
            ### Pass we need to do an upgrade...
            ### We'll implement that later. :-)
            pass

        # Clean out any ranks that don't have tickets.
        cur.execute("DELETE FROM mp_backlog WHERE ticket_id NOT IN "
                    "(SELECT id FROM ticket)")

        cur.execute("SELECT MAX(rank) FROM mp_backlog")
        row = cur.fetchone()

        # If the mp_backlog table is empty, simply start with 1.
        if row[0] is not None:
            rank = row[0] + 1
        else:
            rank = 1

        # Make sure that all tickets have a rank
        cur.execute("SELECT t.id FROM ticket AS t LEFT JOIN mp_backlog "
                    "ON t.id = mp_backlog.ticket_id WHERE mp_backlog.ticket_id "
                    "IS NULL")

        for row in cur.fetchall():
            ticket_id = row[0]

            # Insert a default rank for the ticket, using the ticket id
            cur.execute("INSERT INTO mp_backlog VALUES (%s,%s,%s)",
                        (ticket_id, rank, None))

            rank += 1

        db.commit()

    # IRequestFilter

    def pre_process_request(self, req, handler):
        return handler

    projects_tmpl = """
<form xmlns:py="http://genshi.edgewall.org/" action="" py:if="all_projects" style="display:inline-block;">
$proj
<select id="mp-projects-sel" name="mp_proj">
    <option value="" selected="'' == sel_prj or None}">$all_label</option>
    <option py:for="prj in all_projects" value="$prj" selected="${prj == sel_prj or None}">$prj</option>
</select>
<input type="submit" value="$btn"/>
</form>
"""

    def get_milestone_data(self, req):
        """Get a dictionary holding milestones for each smp project.
        @param req: Request object

        @return: dictionary with project name as key and a list of milestones as value.
        """
        all_projects = self.__SmpModel.get_all_projects_filtered_by_conditions(req)
        milestones_for_project = defaultdict(list)

        for project in sorted(all_projects, key=itemgetter(1)):
            milestones = self.__SmpModel.get_milestones_of_project(project[1])
            for milestone in sorted(milestones, key=itemgetter(0)):
                ms = milestone[0]
                is_completed = self.__SmpModel.is_milestone_completed(ms)
                hide_milestone = is_completed
                if not hide_milestone:
                    milestones_for_project[project[1]].append(ms)
        return milestones_for_project

    def post_process_request(self, req, template, data, content_type):
        if have_smp and template == 'backlog.html':
            all_proj = self.env.config.getlist('ticket-custom', 'project.options', sep='|')

            if all_proj:
                sel_proj = req.args.get('mp_proj', '')
                data['mp_proj'] = sel_proj
                data['ms_for_proj'] = self.get_milestone_data(req)
                sel = MarkupTemplate(self.projects_tmpl)
                add_ctxtnav(req, tag.div(sel.generate(proj=_("Project"), all_projects=all_proj,
                                                      sel_prj=sel_proj, btn=_("Change"), all_label=_('All'))))
        return template, data, content_type

    # INavigationContributor methods

    def get_permission_actions(self):
        return ['BACKLOG_ADMIN']

    def get_active_navigation_item(self, req):
        return 'mpbacklog'

    def get_navigation_items(self, req):
        if 'TICKET_VIEW' in req.perm:
            yield 'mainnav', 'mpbacklog', html.a('Backlog', href=req.href.mpbacklog())

    # ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('mpbacklog', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ITicketChangeListener
    def ticket_created(self, ticket):

        @self.env.with_transaction()
        def do_created(db):
            cursor = db.cursor()
            cursor.execute("SELECT MAX(rank) FROM mp_backlog")
            rank = cursor.fetchone()[0]
            if rank is None:
                rank = 1
            else:
                rank += 1
            cursor.execute("INSERT INTO mp_backlog VALUES (%s, %s, %s)",
                           (ticket.id, rank, None))

    def ticket_changed(self, ticket, comment, author, old_values):
        pass

    def ticket_deleted(self, ticket):

        @self.env.with_transaction()
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute("DELETE FROM mp_backlog WHERE ticket_id = %s",
                           (ticket.id,))

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/mpbacklog(?:/(move_after|move_before|assign|milestone/(?:[^/]+)))?/?',
                         req.path_info)
        if match:
            return True
        return False

    def process_request(self, req):
        
        req.perm.require('TICKET_VIEW')
        if req.method == 'POST':
            req.perm.require('BACKLOG_ADMIN')

            if 'move_after' in req.path_info:
                return self._move_after(req)
            elif 'move_before' in req.path_info:
                return self._move_before(req)
            elif 'assign' in req.path_info:
                return self._assign_milestone(req)
            else:
                raise HTTPBadRequest("Invalid POST request")

        milestone = None
        if req.path_info.startswith('/mpbacklog/milestone/'):
            # Account for '/' in milestone names
            path = req.path_info.split('/')
            if path > 3:
                milestone = "/".join(path[3:])

        if milestone == '(unscheduled)':
            milestone = None

        data = {
            'title': (milestone or "Unscheduled"),
        }

        class Report(object):
            def __init__(self):
                self.id = -1

        data['tickets'] = self._get_active_tickets(milestone)
        data['form_token'] = req.form_token
        data['active_milestones'] = self._get_active_milestones(milestone)
        data['base_path'] = req.base_path
        data['custom_fields'] = [(cf["name"], cf["label"]) for cf in TicketSystem(self.env).get_custom_fields()]
        data['shown_fields'] = req.session.get('backlog_fields') or self._ticket_fields
        custom_fields = [(cf["name"], cf["label"]) for cf in TicketSystem(self.env).get_custom_fields()]
        data['mp_fields'] = self._ticket_fields_sel + custom_fields
        data['shown_fields_sel'] = req.session.get('backlog_fields') or [field[0] for field in self._ticket_fields_sel]

        if 'BACKLOG_ADMIN' in req.perm:
            data['allow_sorting'] = True

        if self.trac_0_12:
            add_script(req, self.env.config.get('trac', 'jquery_ui_location') or
                           'common/js/jquery-ui.js')
            add_stylesheet(req, self.env.config.get('trac', 'jquery_ui_theme_location') or
                           'common/css/jquery-ui/jquery-ui.css')
        else:
            Chrome(self.env).add_jquery_ui(req)

        add_stylesheet(req, 'mpbacklog/css/backlog.css')
        add_script_data(req, {'mp_post_url': req.base_path+'/mpbacklog',
                              'mp_form_token': req.form_token})
        add_script(req, 'mpbacklog/js/backlog.js')
        return 'backlog.html', data, None

    def _get_active_tickets(self, milestone = None):
        db = self.env.get_read_db()
        cursor = db.cursor()

        if milestone is None:
            # Need a separate unscheduled mp_backlog query since deleting a
            # milestone and re-targeting a ticket can set the milestone field
            # to null, instead of the empty string.
            UNSCHEDULED_BACKLOG_QUERY = '''SELECT id FROM ticket t
              LEFT JOIN enum p ON p.name = t.priority AND
                p.type = 'priority'
              LEFT JOIN mp_backlog bp ON bp.ticket_id = t.id
              WHERE status <> 'closed' AND
                (milestone = '' or milestone is null)
              ORDER BY bp.rank, %s, t.type, time
            ''' % db.cast('p.value', 'int')
            cursor.execute(UNSCHEDULED_BACKLOG_QUERY)
        else:
            BACKLOG_QUERY = '''SELECT id FROM ticket t
              LEFT JOIN enum p ON p.name = t.priority AND
                p.type = 'priority'
              LEFT JOIN mp_backlog bp ON bp.ticket_id = t.id
              WHERE status <> 'closed' AND milestone = %%s
              ORDER BY bp.rank, %s, t.type, time
            ''' % db.cast('p.value', 'int')
            cursor.execute(BACKLOG_QUERY, (milestone,))

        tickets = []

        for row in cursor:
            t = Ticket(self.env, row[0])
            tickets.append(t)

        return tickets

    def _move_before(self, req):
        ticket_id = int(req.args.get('ticket_id', 0))
        before_ticket_id = int(req.args.get('before_ticket_id', 0))

        to_result = {}

        try:
            @self.env.with_transaction()
            def do_move(db):
                cursor = db.cursor()

                cursor.execute('SELECT rank FROM mp_backlog WHERE ticket_id = %s',
                               (ticket_id,))
                old_rank = cursor.fetchone()[0]

                cursor.execute('SELECT rank FROM mp_backlog WHERE ticket_id = %s',
                               (before_ticket_id,))
                new_rank = cursor.fetchone()[0]

                if new_rank > old_rank:
                    cursor.execute(
                        'UPDATE mp_backlog SET rank = rank - 1 WHERE rank > %s AND rank < %s',
                        (old_rank, new_rank))
                    new_rank -= 1
                else:
                    cursor.execute(
                        'UPDATE mp_backlog SET rank = rank + 1 WHERE rank >= %s AND rank < %s',
                        (new_rank, old_rank))

                cursor.execute(
                    'UPDATE mp_backlog SET rank = %s WHERE ticket_id = %s',
                    (new_rank, ticket_id))
        except:
            to_result['msg'] = 'Error trying to update rank'

        if 'msg' in to_result:
            to_result['errorcode'] = 202
            req.send_response(202)
        else:
            to_result['errorcode'] = 200
            req.send_response(200)

        data = simplejson.dumps(to_result)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(data))
        req.end_headers()
        req.write(data)


    def _move_after(self, req):
        ticket_id = int(req.args.get('ticket_id', 0))
        after_ticket_id = int(req.args.get('after_ticket_id', 0))

        to_result = {}

        try:
            @self.env.with_transaction()
            def do_move(db):
                cursor = db.cursor()

                cursor.execute('SELECT rank FROM mp_backlog WHERE ticket_id = %s',
                               (ticket_id,))
                old_rank = cursor.fetchone()[0]

                cursor.execute('SELECT rank FROM mp_backlog WHERE ticket_id = %s',
                               (after_ticket_id,))
                new_rank = cursor.fetchone()[0]

                if old_rank < new_rank:
                    cursor.execute(
                        'UPDATE mp_backlog SET rank = rank - 1 WHERE rank > %s AND rank <= %s',
                        (old_rank, new_rank))
                elif old_rank >= new_rank:
                    cursor.execute(
                        'UPDATE mp_backlog SET rank = rank + 1 WHERE rank > %s AND rank <= %s',
                        (new_rank, old_rank))
                    new_rank += 1

                cursor.execute(
                    'UPDATE mp_backlog SET rank = %s WHERE ticket_id = %s',
                    (new_rank, ticket_id))

                db.commit()
        except:
            to_result['msg'] = 'Error trying to update rank'

        self._get_active_tickets()

        if 'msg' in to_result:
            to_result['errorcode'] = 202
            req.send_response(202)
        else:
            to_result['errorcode'] = 200
            req.send_response(200)

        data = simplejson.dumps(to_result)

        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(data))
        req.end_headers()
        req.write(data)

    def _get_num_tickets(self, cursor, milestone):
        cursor.execute(
                "SELECT COUNT(*) FROM ticket WHERE status <> 'closed'"
                "AND COALESCE(milestone, '') = %s", (milestone,))
        return cursor.fetchone()[0]

    def _get_active_milestones(self, exclude = None):
        '''Retrieve a list of milestones.  If exclude is specified, it
        will exclude that milestone from the list and add in the unscheduled
        milestone.'''
        db = self.env.get_read_db()

        cursor = db.cursor()

        results = []

        if exclude:
            num_tickets = self._get_num_tickets(cursor, '')
            results.append(
                dict(name='(unscheduled)', due='--', num_tickets=num_tickets))

        cursor.execute('''SELECT name, due FROM milestone
            WHERE completed = 0
            ORDER BY (due = 0), due, UPPER(name), name''')

        rows = cursor.fetchall()

        for row in rows:
            if exclude and exclude == row[0]:
                continue

            num_tickets = self._get_num_tickets(cursor, row[0])

            d = dict(name=row[0],
                     due=(row[1] and format_date(row[1])) or '--',
                     num_tickets=num_tickets,
                     path=unicode_quote(row[0], safe=''),
                     id='MS'+unicode_to_base64(row[0])  # Make sure element id only contains valid chars
                     )
            results.append(d)

        return results

    def _assign_milestone(self, req):
        ticket_id = int(req.args.get('ticket_id'))
        milestone = unicode_from_base64(req.args.get('milestone', 'MS')[2:])
        author = get_reporter_id(req, 'author')

        if milestone == '(unscheduled)':
            milestone = ''

        to_result = {}

        ticket = None
        try:
            ticket = Ticket(self.env, ticket_id)
        except:
            to_result['msg'] = "Couldn't find ticket!"

        if ticket:
            db = self.env.get_read_db()
            cursor = db.cursor()

            ms_exists = False
            try:
                ms = Milestone(self.env, milestone)
                ms_exists = True
            except ResourceNotFound:
                to_result['msg'] = "Milestone not found."

            if ms_exists:
                try:
                    ticket['milestone'] = milestone
                    ticket.save_changes(author, "")

                    to_result['num_tickets'] = self._get_num_tickets(cursor, milestone)
                except:
                    to_result['msg'] = "Unable to assign milestone"

        if 'msg' in to_result:
            to_result['errorcode'] = 202
            req.send_response(202)
        else:
            to_result['errorcode'] = 200
            req.send_response(200)

        data = simplejson.dumps(to_result)

        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(data))
        req.end_headers()
        req.write(data)
