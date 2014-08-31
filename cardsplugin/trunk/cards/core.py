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
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, web_context

from cards.model import SCHEMA, Card


PLUGIN_NAME = 'CardsPlugin'
PLUGIN_VERSION = 1


class CardsModule(Component):
    """Kanban-style stacks of cards."""

    implements(IPermissionRequestor, IRequestHandler, IEnvironmentSetupParticipant, ITemplateProvider)

    # IPermissionRequestor methods
    
    def get_permission_actions(self):
        return ['CARDS_ADMIN']

    # IRequestHandler methods

    MATCH_REQUEST_RE = re.compile(r'^/card(:/(.+))?$')

    def match_request(self, req):
        match = self.MATCH_REQUEST_RE.match(req.path_info)
        if match:
            if match.group(1):
                req.args['stack'] = match.group(1)
            return True

    def process_request(self, req):
        req.perm.require('CARDS_ADMIN')

        action = req.args.get('action')

        if 'POST' == req.method:
            if action == 'add_card':
                card = self._parse_card(req)
                Card.add(self.env, card)
                self._send_card(req, card)

            elif action == 'update_card':
                card = self._parse_card(req)
                Card.update(self.env, card)
                self._send_card(req, card)

            elif action == 'delete_card':
                card_id = req.args.get('id')
                Card.delete_by_id(self.env, card_id)
                req.send_no_content()
        elif 'GET' == req.method:
            format = req.args.get('format')
            if format == 'json':
                stack_ids = req.args.get('stack', '').split('|')
                cards = Card.select_by_stacks(self.env, stack_ids)
                self._send_cards(req, cards)
        raise TracError()

    def _parse_card(self, req):
        return Card(
            int(req.args.get('id')),
            req.args.get('stack'),
            int(req.args.get('rank')),
            req.args.get('title'))

    def _send_card(self, req, card):
        context = web_context(req, 'cards')
        self._send_json(req, card.serialized(self.env, context))
        
    def _send_cards(self, req, cards):
        context = web_context(req, 'cards')
        self._send_json(req, [c.serialized(self.env, context) for c in cards])

    def _send_json(self, req, data):
        content = JSONEncoder().encode(data).encode('utf-8')
        req.send(content, 'application/json')

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
                upgrades = __import__('cards.upgrades', globals(), locals(), [modulename])
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
        return [('cards', pkg_resources.resource_filename('cards', 'htdocs'))]

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('cards', 'templates')]
