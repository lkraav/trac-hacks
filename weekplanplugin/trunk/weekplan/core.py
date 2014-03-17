# -*- coding: utf-8 -*-

import datetime
from json.encoder import JSONEncoder
import pkg_resources
import re
from StringIO import StringIO

from trac import __version__
from trac.db.api import DatabaseManager
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler, RequestDone
from trac.web.chrome import ITemplateProvider, web_context
from trac.util.datefmt import format_date, format_datetime, parse_date, utc
from trac.util.text import CRLF

from weekplan.model import SCHEMA, WeekPlanEvent


PLUGIN_NAME = 'WeekPlanPlugin'
PLUGIN_VERSION = 1


class WeekPlanModule(Component):
    """Week-by-week plans."""

    implements(IPermissionRequestor, IRequestHandler, IEnvironmentSetupParticipant, ITemplateProvider)

    # IPermissionRequestor methods
    
    def get_permission_actions(self):
        return ['WEEK_PLAN']

    # IRequestHandler methods

    MATCH_REQUEST_RE = re.compile(r'^/weekplan(:/(.+))?$')

    def match_request(self, req):
        match = self.MATCH_REQUEST_RE.match(req.path_info)
        if match:
            if match.group(1):
                req.args['plan'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.require('WEEK_PLAN')

        action = req.args.get('action')

        if 'POST' == req.method:
            if action == 'add_event':
                event = self._parse_event(req)
                WeekPlanEvent.add(self.env, event)
                self._send_event(req, event)

            elif action == 'update_event':
                event = self._parse_event(req)
                WeekPlanEvent.update(self.env, event)
                self._send_event(req, event)

            elif action == 'delete_event':
                event_id = req.args.get('id')
                WeekPlanEvent.delete_by_id(self.env, event_id)
                req.send_no_content()
        elif 'GET' == req.method:
            format = req.args.get('format')
            if format == 'ics':
                plan_id = req.args.get('plan')
                events = WeekPlanEvent.select_by_plan(self.env, plan_id)
                self._render_ics(req, plan_id, events)
        raise TracError()

    def _parse_event(self, req):
        return WeekPlanEvent(
            req.args.get('id'),
            req.args.get('plan'),
            req.args.get('title'),
            parse_date(req.args.get('start')),
            parse_date(req.args.get('end')))

    def _send_event(self, req, event):
        context = web_context(req, 'weekplan')
        self._send_json(req, event.serialized(self.env, context))

    def _send_json(self, req, data):
        content = JSONEncoder().encode(data).encode('utf-8')
        req.send(content, 'application/json')

    # Derived from http://trac.edgewall.org/browser/tags/trac-1.1.1/trac/ticket/roadmap.py?marks=466-580#L466
    def _render_ics(self, req, plan_id, events):
        req.send_response(200)
        req.send_header('Content-Type', 'text/calendar;charset=utf-8')
        buf = StringIO()

        def escape_value(text):
            s = ''.join(map(lambda c: '\\' + c if c in ';,\\' else c, text))
            return '\\n'.join(re.split(r'[\r\n]+', s))

        def write_prop(name, value, params={}):
            text = ';'.join([name] + [k + '=' + v for k, v in params.items()]) \
                 + ':' + escape_value(value)
            firstline = 1
            while text:
                if not firstline:
                    text = ' ' + text
                else:
                    firstline = 0
                buf.write(text[:75] + CRLF)
                text = text[75:]

        def write_date(name, value, params={}):
            params['VALUE'] = 'DATE'
            write_prop(name, format_date(value, '%Y%m%d', req.tz), params)

        def write_utctime(name, value, params={}):
            write_prop(name, format_datetime(value, '%Y%m%dT%H%M%SZ', utc),
                       params)

        host = req.base_url[req.base_url.find('://') + 3:]
        user = req.args.get('user', 'anonymous')

        write_prop('BEGIN', 'VCALENDAR')
        write_prop('VERSION', '2.0')
        write_prop('PRODID', '-//Edgewall Software//NONSGML Trac %s//EN'
                   % __version__)
        write_prop('METHOD', 'PUBLISH')
        write_prop('X-WR-CALNAME',
                   self.env.project_name + ' - WeekPlan ' + plan_id)
        write_prop('X-WR-CALDESC', self.env.project_description)
        write_prop('X-WR-TIMEZONE', str(req.tz))

        for event in events:
            uid = '<%s/%s/%s@%s>' % (req.base_path, plan_id, event.id, host)

            write_prop('BEGIN', 'VEVENT')
            write_prop('UID', uid)
            write_utctime('DTSTAMP', datetime.datetime.now())
            write_date('DTSTART', event.start)
            write_date('DTEND', event.end)
            write_prop('SUMMARY', event.title)
            # write_prop('URL', req.abs_href.weekplan(plan_id, event.id))
            # write_prop('DESCRIPTION', event.description)
            write_prop('END', 'VEVENT')

        write_prop('END', 'VCALENDAR')

        ics_str = buf.getvalue().encode('utf-8')
        req.send_header('Content-Length', len(ics_str))
        req.end_headers()
        req.write(ics_str)
        raise RequestDone

    # IEnvironmentSetupParticipant

    def environment_created(self):
        db_connector, _ = DatabaseManager(self.env).get_connector()
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in SCHEMA:
                for stmt in db_connector.to_sql(table): 
                    cursor.execute(stmt) 
            cursor.execute(""" 
                INSERT INTO system (name, value) 
                VALUES (%s, %s) 
                """, (PLUGIN_NAME, PLUGIN_VERSION)) 

    def environment_needs_upgrade(self, db):
        rows = self.env.db_query("""
                SELECT value FROM system WHERE name='%s'
                """ % PLUGIN_NAME)
        dbver = int(rows[0][0]) if rows else 0
        if dbver == PLUGIN_VERSION:
            return False
        elif dbver > PLUGIN_VERSION:
            self.env.log.info("%s database schema version is %s, should be %s",
                         PLUGIN_NAME, dbver, PLUGIN_VERSION)
        return True

    def upgrade_environment(self, db):
        db_connector, _ = DatabaseManager(self.env).get_connector() 
        cursor = db.cursor()
        for table in SCHEMA:
            for stmt in db_connector.to_sql(table): 
                cursor.execute(stmt) 
        cursor.execute(""" 
            INSERT INTO system (name, value) 
            VALUES (%s, %s) 
            """, (PLUGIN_NAME, PLUGIN_VERSION))

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('weekplan', pkg_resources.resource_filename('weekplan', 'htdocs'))]

    def get_templates_dirs(self):
        return []
