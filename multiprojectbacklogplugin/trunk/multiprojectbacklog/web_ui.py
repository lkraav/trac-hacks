# -*- coding: utf-8 -*-
#
# Copyright (C) 2009, 2011, 2013 John Szakmeister
# Copyright (C) 2016-2021 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import json
import re
from collections import defaultdict
from operator import itemgetter
from pkg_resources import get_distribution, parse_version

from genshi.template.markup import MarkupTemplate
from trac.core import *
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.ticket.api import ITicketChangeListener, TicketSystem
from trac.ticket.model import Milestone, Ticket
from trac.util import get_reporter_id
from trac.util.datefmt import format_date
from trac.util.html import html
from trac.util.text import unicode_quote, unicode_from_base64, unicode_to_base64
from trac.util.translation import _
from trac.web.chrome import Chrome, INavigationContributor, ITemplateProvider, \
    ResourceNotFound, add_ctxtnav, add_script, add_script_data, add_stylesheet
from trac.web.api import HTTPBadRequest, IRequestFilter
from trac.web.main import IRequestHandler

from multiprojectbacklog.schema import schema_version, schema

try:
    from simplemultiproject.model import SmpModel
except ImportError:
    have_smp = False
else:
    have_smp = True


class MultiProjectBacklog(Component):
    implements(INavigationContributor, IRequestHandler, IRequestFilter,
               IEnvironmentSetupParticipant, ITemplateProvider,
               ITicketChangeListener, IPermissionRequestor)

    _ticket_fields = [
        u'id', u'summary', u'component', u'version', u'type', u'owner',
        u'status',
        u'time_created'
    ]
    _ticket_fields_sel = [
        (u'id', u'Id'), (u'summary', u'Summary'), (u'component', u'Component'),
        (u'version', u'Version'), (u'type', u'Type'), (u'owner', u'Owner'),
        (u'status', u'Status'), (u'time_created', u'Created')
    ]

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')

    def __init__(self):
        if have_smp:
            self.__SmpModel = SmpModel(self.env)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        connector, args = DatabaseManager(self.env).get_connector()
        to_sql = connector.to_sql

        with self.env.db_transaction as db:
            for table in schema:
                sql = to_sql(table)
                for stmt in sql:
                    db(stmt)

            # Insert version information
            db("""
                INSERT INTO system (name,value)
                VALUES ('mp_backlog_version', %s)
                """, (schema_version,))

    def environment_needs_upgrade(self, db=None):
        with self.env.db_query as db:
            for version, in db("""
                    SELECT value FROM system WHERE name='mp_backlog_version'
                    """):
                if int(version) < schema_version:
                    return True
                break
            else:
                return True

            for count, in db("""
                    SELECT COUNT(*) FROM mp_backlog
                    LEFT JOIN ticket ON ticket.id = mp_backlog.ticket_id
                    WHERE ticket.id IS NULL
                    """):
                if count:
                    return True

            for count, in db("""
                    SELECT COUNT(*) FROM ticket AS t
                     LEFT JOIN mp_backlog ON t.id = mp_backlog.ticket_id
                    WHERE mp_backlog.ticket_id IS NULL
                    """):
                if count:
                    return True

            return False

    def upgrade_environment(self, db=None):
        with self.env.db_transaction as db:
            for version in db("""
                    SELECT value FROM system WHERE name='mp_backlog_version'
                    """):
                if int(version) < schema_version:
                    # Pass we need to do an upgrade...
                    # We'll implement that later.
                    pass
                break
            else:
                self.environment_created()

            # Clean out any ranks that don't have tickets.
            db("""
                DELETE FROM mp_backlog
                WHERE ticket_id NOT IN (SELECT id FROM ticket)
                """)

            for rank, in db("SELECT MAX(rank) FROM mp_backlog"):
                # If the mp_backlog table is empty, simply start with 1.
                if rank is not None:
                    rank += 1
            else:
                rank = 1

            # Make sure that all tickets have a rank
            for ticket_id, in db("""
                    SELECT t.id FROM ticket AS t
                     LEFT JOIN mp_backlog ON t.id = mp_backlog.ticket_id
                    WHERE mp_backlog.ticket_id IS NULL
                    """):
                # Insert a default rank for the ticket, using the ticket id
                db("INSERT INTO mp_backlog VALUES (%s,%s,%s)",
                   (ticket_id, rank, None))
                rank += 1

    # IRequestFilter methods

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

        @return: dictionary with project name as key and a list of milestones
                 as value.
        """
        all_projects = self.__SmpModel.get_all_projects_filtered_by_conditions(
            req)
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
        if have_smp and template in ('backlog.html', 'mp_backlog_jinja.html'):
            all_proj = self.env.config.getlist('ticket-custom',
                                               'project.options', sep='|')

            if all_proj:
                sel_proj = req.args.get('mp_proj', '')
                data['mp_proj'] = sel_proj
                data['ms_for_proj'] = self.get_milestone_data(req)
                sel = MarkupTemplate(self.projects_tmpl)
                add_ctxtnav(req, html.div(
                    sel.generate(proj=_("Project"), all_projects=all_proj,
                                 sel_prj=sel_proj, btn=_("Change"),
                                 all_label=_('All'))))
        return template, data, content_type

    # INavigationContributor methods

    def get_permission_actions(self):
        return ['BACKLOG_ADMIN']

    def get_active_navigation_item(self, req):
        return 'mpbacklog'

    def get_navigation_items(self, req):
        if 'TICKET_VIEW' in req.perm:
            yield 'mainnav', 'mpbacklog', html.a('Backlog',
                                                 href=req.href.mpbacklog())

    # ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('mpbacklog', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ITicketChangeListener methods

    def ticket_created(self, ticket):

        with self.env.db_transaction as db:
            for rank, in db("SELECT MAX(rank) FROM mp_backlog"):
                if rank:
                    rank += 1
                    break
            else:
                rank = 1
            db("""
                INSERT INTO mp_backlog VALUES (%s, %s, %s)
                """, (ticket.id, rank, None))

    def ticket_changed(self, ticket, comment, author, old_values):
        pass

    def ticket_deleted(self, ticket):

        self.env.db_transaction("""
            DELETE FROM mp_backlog WHERE ticket_id = %s
            """, (ticket.id,))

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/mpbacklog(?:/(move_after|move_before|assign|'
                         r'milestone/(?:[^/]+)))?/?', req.path_info)
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
            'title': milestone or "Unscheduled",
            'tickets': self._get_active_tickets(milestone),
            'form_token': req.form_token,
            'active_milestones': self._get_active_milestones(milestone),
            'custom_fields': [(cf["name"], cf["label"]) for cf in
                              TicketSystem(self.env).get_custom_fields()],
            'shown_fields': req.session.get(
                'backlog_fields') or self._ticket_fields
        }

        custom_fields = [(cf["name"], cf["label"]) for cf in
                         TicketSystem(self.env).get_custom_fields()]
        data['mp_fields'] = self._ticket_fields_sel + custom_fields
        data['shown_fields_sel'] = req.session.get('backlog_fields') or [
            field[0] for field in self._ticket_fields_sel]

        if 'BACKLOG_ADMIN' in req.perm:
            data['allow_sorting'] = True

        Chrome(self.env).add_jquery_ui(req)

        add_stylesheet(req, 'mpbacklog/css/backlog.css')
        add_script_data(req, {'mp_post_url': req.base_path + '/mpbacklog',
                              'mp_form_token': req.form_token})
        add_script(req, 'mpbacklog/js/backlog.js')
        if self.pre_1_3:
            return 'backlog.html', data, None
        else:
            return 'mp_backlog_jinja.html', data, {}

    def _get_active_tickets(self, milestone=None):
        with self.env.db_query as db:
            if milestone is None:
                # Need a separate unscheduled mp_backlog query since deleting
                # a milestone and re-targeting a ticket can set the milestone
                # field to null, instead of the empty string.
                query = """
                    SELECT id FROM ticket t
                     LEFT JOIN enum p
                      ON p.name = t.priority AND p.type = 'priority'
                     LEFT JOIN mp_backlog bp ON bp.ticket_id = t.id
                    WHERE status <> 'closed' AND
                     (milestone = '' or milestone is null)
                    ORDER BY bp.rank, %s, t.type, time
                    """ % db.cast('p.value', 'int')
                args = []
            else:
                query = """
                    SELECT id FROM ticket t
                     LEFT JOIN enum p
                      ON p.name = t.priority AND p.type = 'priority'
                     LEFT JOIN mp_backlog bp ON bp.ticket_id = t.id
                    WHERE status <> 'closed' AND milestone = %%s
                    ORDER BY bp.rank, %s, t.type, time
                    """ % db.cast('p.value', 'int')
                args = (milestone,)

            return [Ticket(self.env, row[0])
                    for row in self.env.db_query(query, args)]

    def _move_before(self, req):
        ticket_id = int(req.args.get('ticket_id', 0))
        before_ticket_id = int(req.args.get('before_ticket_id', 0))

        to_result = {}

        try:
            with self.env.db_transaction as db:
                old_rank = None
                for old_rank, in db("""
                        SELECT rank FROM mp_backlog WHERE ticket_id = %s
                        """, (ticket_id,)):
                    break

                new_rank = None
                for new_rank, in db("""
                        SELECT rank FROM mp_backlog WHERE ticket_id = %s
                        """, (before_ticket_id,)):
                    break

                if new_rank > old_rank:
                    db("""
                        UPDATE mp_backlog SET rank = rank - 1
                        WHERE rank > %s AND rank < %s
                        """, (old_rank, new_rank))
                    new_rank -= 1
                else:
                    db("""
                        UPDATE mp_backlog SET rank = rank + 1
                        WHERE rank >= %s AND rank < %s
                        """, (new_rank, old_rank))

                db("""
                    UPDATE mp_backlog SET rank = %s WHERE ticket_id = %s
                    """, (new_rank, ticket_id))
        except:
            to_result['msg'] = "Error trying to update rank"

        if 'msg' in to_result:
            to_result['errorcode'] = 202
            req.send_response(202)
        else:
            to_result['errorcode'] = 200
            req.send_response(200)

        data = json.dumps(to_result)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(data))
        req.end_headers()
        req.write(data)

    def _move_after(self, req):
        ticket_id = int(req.args.get('ticket_id', 0))
        after_ticket_id = int(req.args.get('after_ticket_id', 0))

        to_result = {}

        try:
            with self.env.db_transaction as db:
                old_rank = None
                for old_rank, in db("""
                        SELECT rank FROM mp_backlog WHERE ticket_id = %s
                        """, (ticket_id,)):
                    break

                new_rank = None
                for new_rank, in db("""
                        SELECT rank FROM mp_backlog WHERE ticket_id = %s
                        """, (after_ticket_id,)):
                    break

                if old_rank < new_rank:
                    db("""
                        UPDATE mp_backlog SET rank = rank - 1
                        WHERE rank > %s AND rank <= %s
                        """, (old_rank, new_rank))
                elif old_rank >= new_rank:
                    db("""
                        UPDATE mp_backlog SET rank = rank + 1
                        WHERE rank > %s AND rank <= %s
                        """, (new_rank, old_rank))
                    new_rank += 1

                db("""
                    UPDATE mp_backlog SET rank = %s WHERE ticket_id = %s
                    """, (new_rank, ticket_id))

        except:
            to_result['msg'] = 'Error trying to update rank'

        self._get_active_tickets()

        if 'msg' in to_result:
            to_result['errorcode'] = 202
            req.send_response(202)
        else:
            to_result['errorcode'] = 200
            req.send_response(200)

        data = json.dumps(to_result)

        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(data))
        req.end_headers()
        req.write(data)

    def _get_num_tickets(self, milestone):
        for count, in self.env.db_query("""
                SELECT COUNT(*) FROM ticket
                WHERE status <> 'closed' AND COALESCE(milestone, '') = %s
                """, (milestone,)):
            return count

    def _get_active_milestones(self, exclude=None):
        """Retrieve a list of milestones.  If exclude is specified, it
        will exclude that milestone from the list and add in the unscheduled
        milestone."""
        results = []
        if exclude:
            num_tickets = self._get_num_tickets('')
            results.append(
                dict(name='(unscheduled)', due='--', num_tickets=num_tickets))

        for name, due in self.env.db_query("""
                SELECT name, due FROM milestone WHERE completed = 0
                ORDER BY (due = 0), due, UPPER(name), name
                """):
            if exclude and exclude == name:
                continue

            num_tickets = self._get_num_tickets(name)

            d = {
                'name': name,
                'due': format_date(due) if due else '--',
                'num_tickets': num_tickets,
                'id': 'MS' + unicode_to_base64(name)
            }
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
            ms_exists = False
            try:
                Milestone(self.env, milestone)
            except ResourceNotFound:
                to_result['msg'] = "Milestone not found."
            else:
                ms_exists = True

            if ms_exists:
                try:
                    ticket['milestone'] = milestone
                    ticket.save_changes(author, "")
                    to_result['num_tickets'] = self._get_num_tickets(milestone)
                except:
                    to_result['msg'] = "Unable to assign milestone"

        if 'msg' in to_result:
            to_result['errorcode'] = 202
            req.send_response(202)
        else:
            to_result['errorcode'] = 200
            req.send_response(200)

        data = json.dumps(to_result)

        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(data))
        req.end_headers()
        req.write(data)
