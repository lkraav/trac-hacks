# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Richard Liao <richard.liao.i@gmail.com>
# Copyright (C) 2014-2017 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from pkg_resources import resource_filename

from genshi.filters.transform import Transformer
from trac.admin.api import IAdminCommandProvider
from trac.config import IntOption
from trac.core import implements
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Table
from trac.env import IEnvironmentSetupParticipant
from trac.resource import Resource
from trac.versioncontrol.api import RepositoryManager
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import Chrome, ITemplateProvider, add_stylesheet, \
                            web_context
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import format_datetime, from_utimestamp, user_time
from trac.util.text import shorten_line
from trac.util.translation import domain_functions
from tracopt.ticket.commit_updater import CommitTicketUpdater

gettext, _, tag_, N_, add_domain = \
    domain_functions('ticketlog', 'gettext', '_', 'tag_', 'N_', 'add_domain')


class TicketLogModule(CommitTicketUpdater):
    implements(IAdminCommandProvider, IEnvironmentSetupParticipant,
               ITemplateProvider, ITemplateStreamFilter)

    max_message_length = IntOption('ticketlog', 'log_message_maxlength',
        doc="""Maximum length of log message to display.""")

    db_version = 1
    db_version_key = 'ticketlog_version'

    schema = [
        Table('ticket_revision', key=['ticket', 'repos', 'rev'])[
            Column('ticket', 'int'),
            Column('repos', type='int'),
            Column('rev', key_size=40)
        ],
    ]

    def __init__(self):
        try:
            locale_dir = resource_filename(__name__, 'locale')
        except KeyError:
            pass
        else:
            add_domain(self.env.path, locale_dir)

    # IAdminCommandProvider methods

    def get_admin_commands(self):
        yield ('ticketlog sync', '',
               "Sync the ticket-revision table for the ticket log.",
               None, self._do_sync)

    def _do_sync(self):
        last_cset_id = None
        with self.env.db_transaction as db:
            db("""
                DELETE FROM ticket_revision
                """)
            for repos, rev, message, author, time in db("""
                    SELECT repos,rev,message,author,time
                    FROM revision
                    """):
                self.log.info("Trying to sync revision %s", rev)
                cset_id = rev, message, author, time
                if cset_id != last_cset_id:
                    self._insert_revision(repos, rev, message)
                    last_cset_id = cset_id

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(self.db_version, self.db_version_key)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        dbm.create_tables(self.schema)
        dbm.set_database_version(self.db_version, self.db_version_key)

    # IRepositoryChangeListener methods

    def changeset_added(self, repos, changeset):
        if self._is_duplicate(changeset):
            return
        rev = repos.db_rev(changeset.rev)
        self._insert_revision(repos.id, rev, changeset.message)

    def changeset_modified(self, repos, changeset, old_changeset):
        if self._is_duplicate(changeset):
            return
        tickets = self._parse_message(changeset.message)
        rev = repos.db_rev(changeset.rev)
        with self.env.db_transaction as db:
            old_tickets = set(tid for tid, in db("""
                SELECT ticket FROM ticket_revision
                WHERE repos=%s and rev=%s
                """, (repos.id, rev)))
            added_tickets = set(tickets) - old_tickets
            for tid in added_tickets:
                db("""
                    INSERT INTO ticket_revision (ticket,repos,rev)
                    VALUES (%s,%s,%s)
                    """, (tid, repos.id, rev))
            removed_ticket = old_tickets - set(tickets)
            for tid in removed_ticket:
                db("""
                    DELETE FROM ticket_revision
                    WHERE ticket=%s AND repos=%s AND rev=%s
                    """, (tid, repos.id, rev))

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('ticketlog', resource_filename(__name__, 'htdocs'))]

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' and \
                req.path_info.startswith('/ticket/'):
            ticket_id = req.args.getint('id')
            resource = Resource('ticket', ticket_id)
            if 'CHANGESET_VIEW' in req.perm(resource):
                add_stylesheet(req, 'ticketlog/ticketlog.css')
                revisions = self._get_ticket_revisions(req, ticket_id)
                template = Chrome(self.env) \
                    .load_template('ticketlog.html', None) \
                    .generate(revisions=revisions)
                stream |= Transformer('//div[@id="ticket"]').after(template)
        return stream

    # Internal methods

    def _insert_revision(self, rid, rev, message):
        tickets = self._parse_message(message)
        with self.env.db_transaction as db:
            for tid in tickets:
                db("""
                    INSERT INTO ticket_revision (ticket,repos,rev)
                    VALUES (%s,%s,%s)
                    """, (tid, rid, rev))

    def _get_ticket_revisions(self, req, ticket_id):
        revisions = []

        if not ticket_id:
            return revisions

        rm = RepositoryManager(self.env)
        intermediate = {}
        for row in self.env.db_query("""
                SELECT p.value, r.rev, r.author, r.time, r.message
                FROM ticket_revision AS tr
                 LEFT JOIN revision AS r
                  ON r.repos=tr.repos AND r.rev=tr.rev
                 LEFT JOIN repository AS p
                  ON p.id=tr.repos AND p.name='name'
                WHERE tr.ticket=%s
                """, (ticket_id,)):
            repos_name = row[0]
            rev = row[1]
            author = row[2]
            timestamp = row[3]
            message = row[4]

            repos = rm.get_repository(repos_name)
            drev = repos.display_rev(rev)
            if repos_name:
                link = '[changeset:"%s/%s"]' % (drev, repos_name)
            else:
                link = '[changeset:%s]' % drev
            # Using (rev, author, time, message) as the key
            # If branches from the same repo are under Trac system
            # Only one changeset will be in the ticket changelog
            intermediate[(rev, author, timestamp, message)] = link

        ctxt = web_context(req)
        for key in intermediate:
            rev, author, timestamp, message = key
            if self.max_message_length \
                    and len(message) > self.max_message_length:
                message = shorten_line(message, self.max_message_length)
            link = intermediate[key]
            revision = {
                'rev': format_to_oneliner(self.env, ctxt, link),
                'author': Chrome(self.env).format_author(req, author),
                'timestamp': timestamp,
                'time': user_time(req, format_datetime,
                                  from_utimestamp(timestamp)),
                'message': format_to_html(self.env, ctxt, message),
            }
            revisions.append(revision)

        revisions.sort(key=lambda r: r['timestamp'], reverse=True)

        return revisions
