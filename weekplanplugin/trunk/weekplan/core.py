# -*- coding: utf-8 -*-

import datetime
from json.encoder import JSONEncoder
import pkg_resources
import re
from StringIO import StringIO

from trac import __version__
from trac.db.api import DatabaseManager
from trac.config import OrderedExtensionsOption, ExtensionOption
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler, RequestDone
from trac.web.chrome import ITemplateProvider, web_context
from trac.util.datefmt import format_date, format_datetime, parse_date, utc
from trac.util.text import CRLF

from weekplan.model import SCHEMA, WeekPlanEvent


PLUGIN_NAME = 'WeekPlanPlugin'
PLUGIN_VERSION = 2


class IWeekPlanEventProvider(Interface):
    
    def get_plan_prefixes():
        """Get all plan id prefixes handled by this provider.
        
        :return: a list of plan id prefix strings.
        """
    
    def get_events(plans_ids, range):
        """Get all events for the given plans that the provider handles.

        :param plan_ids: a list of plan id's for which events should be returned.
        :param range: a tuple (datetime, datetime) or None to get all events.
        
        :return: a list of  WeekPlanEvent items.
        """

    def add_event(event):
        """Add a new event. Optional method.
        
        :param event: a new WeekPlanEvent to be added.
        """

    def update_event(event):
        """Update an event. Optional method.
        
        :param event: a WeekPlanEvent to be updated.
        """

    def delete_event(event):
        """Delete an event. Optional method.
        
        :param event: a WeekPlanEvent to be deleted.
        """


class DBWeekPlanEventProvider(Component):
    """Provides events from the dedicated DB table."""
    
    implements(IWeekPlanEventProvider)
    
    def get_plan_prefixes(self):
        return ['db:']
    
    def get_events(self, plan_ids, range):
        if range:
            return WeekPlanEvent.select_by_plans_and_time(self.env, plan_ids, range[0], range[1])
        elif len(plan_ids) == 1:
            return WeekPlanEvent.select_by_plan(self.env, plan_ids[0])
        elif db_plan_ids:
            return WeekPlanEvent.select_by_plans(self.env, plan_ids)
        else:
            return []

    def add_event(self, event):
        WeekPlanEvent.add(self.env, event)

    def update_event(self, event):
        WeekPlanEvent.update(self.env, event)

    def delete_event(self, event):
        WeekPlanEvent.delete_by_id(self.env, event.id)


class WeekPlanModule(Component):
    """Week-by-week plans."""

    implements(IPermissionRequestor, IRequestHandler, IEnvironmentSetupParticipant, ITemplateProvider)

    event_providers = OrderedExtensionsOption('weekplan', 'event_providers',
        IWeekPlanEventProvider,
        'DBWeekPlanEventProvider',
        True,
        """List of components implementing `IWeekPlanEventProvider`.""")

    default_event_provider = ExtensionOption('weekplan', 'default_event_provider',
        IWeekPlanEventProvider,
        'DBWeekPlanEventProvider',
        """Default component handling plans if no prefix matches.""")


    def get_event_provider(self, plan_id):
        for provider in self.event_providers:
            for prefix in provider.get_plan_prefixes():
                if plan_id.startswith(prefix):
                    return provider
        return self.default_event_provider

    def get_events(self, plan_ids, range=None):
        events = []
        remaining_ids = set(plan_ids)
        for provider in self.event_providers:
            prefixes = provider.get_plan_prefixes()
            ids = [id for id in remaining_ids
                      for prefix in prefixes
                      if id.startswith(prefix)]
            remaining_ids -= set(ids)
            if ids:
                events.extend(provider.get_events(ids, range))
        if remaining_ids:
            provider = self.default_event_provider
            ids = list(remaining_ids)
            events.extend(provider.get_events(ids, range))
        return events

    def can_plan_add_event(self, plan_id):
        return hasattr(self.get_event_provider(plan_id), 'add_event')

    def can_plan_update_event(self, plan_id):
        return hasattr(self.get_event_provider(plan_id), 'update_event')

    def can_plan_delete_event(self, plan_id):
        return hasattr(self.get_event_provider(plan_id), 'delete_event')

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
                provider = self.get_event_provider(event.plan)
                provider.add_event(event)
                self._send_event(req, event)

            elif action == 'update_event':
                event = self._parse_event(req)
                provider = self.get_event_provider(event.plan)
                provider.update_event(event)
                self._send_event(req, event)

            elif action == 'delete_event':
                event = self._parse_event(req)
                provider = self.get_event_provider(event.plan)
                provider.delete_event(event)
                req.send_no_content()

        elif 'GET' == req.method:
            format = req.args.get('format')
            if format == 'ics':
                plan_id = req.args.get('plan')
                events = self.get_events([plan_id])
                self._render_ics(req, plan_id, events)
            elif format == 'json':
                plan_ids = req.args.get('plan', '').split('|')
                start = parse_date(req.args.get('start'), utc)
                end = parse_date(req.args.get('end'), utc)
                events = self.get_events(plan_ids, (start, end))
                self._send_events(req, events)
        raise TracError()

    def _parse_event(self, req):
        return WeekPlanEvent(
            req.args.get('id'),
            req.args.get('plan'),
            req.args.get('title'),
            parse_date(req.args.get('start'), utc),
            parse_date(req.args.get('end'), utc))

    def _send_event(self, req, event):
        context = web_context(req, 'weekplan')
        self._send_json(req, event.serialized(self.env, context))
        
    def _send_events(self, req, events):
        context = web_context(req, 'weekplan')
        self._send_json(req, [e.serialized(self.env, context) for e in events])

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
        dbver = self.get_db_version()
        if dbver == PLUGIN_VERSION:
            return False
        elif dbver > PLUGIN_VERSION:
            self.env.log.info("%s database schema version is %s, should be %s",
                         PLUGIN_NAME, dbver, PLUGIN_VERSION)
        return True

    def upgrade_environment(self, db):
        db_connector, _ = DatabaseManager(self.env).get_connector() 
        cursor = db.cursor()
        dbver = self.get_db_version()
        if dbver == 0:
            self.env.log.info("Initialize %s database schema to version %s",
                         PLUGIN_NAME, PLUGIN_VERSION)
            for table in SCHEMA:
                for stmt in db_connector.to_sql(table):
                    cursor.execute(stmt)
            cursor.execute("""
                INSERT INTO system (name, value)
                VALUES (%s, %s)
                """, (PLUGIN_NAME, PLUGIN_VERSION))
        else:
            while dbver != PLUGIN_VERSION:
                dbver = dbver + 1
                self.env.log.info("Upgrade %s database schema to version %s",
                         PLUGIN_NAME, dbver)
                modulename = 'db%i' % dbver
                upgrades = __import__('weekplan.upgrades', globals(), locals(), [modulename])
                script = getattr(upgrades, modulename)
                script.do_upgrade(self.env, dbver, cursor)
            cursor.execute("""
                UPDATE system
                SET value=%s
                WHERE name=%s
                """, (PLUGIN_VERSION, PLUGIN_NAME))

    def get_db_version(self):
        rows = self.env.db_query("""
                SELECT value FROM system WHERE name='%s'
                """ % PLUGIN_NAME)
        return int(rows[0][0]) if rows else 0

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('weekplan', pkg_resources.resource_filename('weekplan', 'htdocs'))]

    def get_templates_dirs(self):
        return []
