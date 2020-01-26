# -*- coding: utf-8 -*-

import datetime
from json.encoder import JSONEncoder
import pkg_resources
import re
try:
    from StringIO import StringIO # Python 2
except ImportError:
    from io import StringIO # Python 3

from trac import __version__
from trac.db.api import DatabaseManager
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, web_context

from cards.model import SCHEMA, Card, CardStack


PLUGIN_NAME = 'CardsPlugin'
PLUGIN_VERSION = 3


def serialized_stacks_by_name(stacks, stack_names):
    stacks_by_name = dict((stack.name, stack.serialized()) for stack in stacks)
    for name in stack_names:
        stacks_by_name.setdefault(name, CardStack(name, 0).serialized())
    return stacks_by_name


def serialized_cards_by_id(cards, env, context):
    return dict((card.id, card.serialized(env, context)) for card in cards)


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
                stack = self._parse_stack(req)
                if not Card.add(self.env, card, stack):
                    self._send_conflict(req)
                self._send_card(req, card)

            elif action == 'update_card':
                card = self._parse_card(req)
                new_stack = self._parse_stack(req)
                old_stack = self._parse_stack(req, True)
                if not Card.update(self.env, card, new_stack, old_stack):
                    self._send_conflict(req)
                self._send_card(req, card)

            elif action == 'delete_card':
                card = self._parse_card(req)
                stack = self._parse_stack(req)
                if not Card.delete_by_id(self.env, card.id, stack):
                    self._send_conflict(req)
                req.send_no_content()
        elif 'GET' == req.method:
            format = req.args.get('format')
            if format == 'json':
                stack_names = req.args.get('stack', '').split('|')
                cards = Card.select_by_stacks(self.env, stack_names)
                stacks = CardStack.select_by_names(self.env, stack_names)
                self._send_cards_and_stacks(req, cards, stacks, stack_names)
        self._send_error(req, 'Bad request', 400)

    def _parse_card(self, req):
        return Card(
            int(req.args.get('id')),
            req.args.get('stack'),
            int(req.args.get('rank')),
            req.args.get('title'),
            req.args.get('color'))

    def _parse_stack(self, req, old=False):
        return CardStack(
            req.args.get('old_stack_name' if old else 'stack'),
            int(req.args.get('old_stack_version' if old else 'stack_version')))

    def _send_card(self, req, card):
        context = web_context(req, 'cards')
        self._send_json(req, card.serialized(self.env, context))
        
    def _send_cards_and_stacks(self, req, cards, stacks, stack_names):
        context = web_context(req, 'cards')
        data = {
            'cards_by_id': serialized_cards_by_id(cards, self.env, context),
            'stacks_by_name': serialized_stacks_by_name(stacks, stack_names),
        }
        self._send_json(req, data)

    def _send_json(self, req, data, status=200):
        content = JSONEncoder().encode(data).encode('utf-8')
        req.send(content, 'application/json', status)
        
    def _send_error(self, req, message, status):
        self._send_json(req, {'message': message}, status)

    def _send_conflict(self, req):
        self._send_error(req, 'Conflicting version. Please refresh', 409)

    # IEnvironmentSetupParticipant

    def environment_created(self):
        dbm = DatabaseManager(self.env)
        dbm.create_tables(SCHEMA)
        dbm.set_database_version(PLUGIN_VERSION, PLUGIN_NAME)

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(PLUGIN_VERSION, PLUGIN_NAME)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        if dbm.get_database_version(PLUGIN_NAME) == 0:
            dbm.create_tables(SCHEMA)
            dbm.set_database_version(PLUGIN_VERSION, PLUGIN_NAME)
        else:
            dbm.upgrade(PLUGIN_VERSION, PLUGIN_NAME, 'cards.upgrades')

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('cards', pkg_resources.resource_filename('cards', 'htdocs'))]

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('cards', 'templates')]
