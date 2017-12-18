# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from __future__ import with_statement

import os
import sys

from trac.admin.api import IAdminCommandProvider
from trac.core import Component, TracError, implements
from trac.resource import ResourceNotFound
from trac.ticket.model import Milestone, Ticket
from trac.util.datefmt import from_utimestamp
from trac.util.text import console_print, exception_to_unicode
from trac.versioncontrol.api import RepositoryManager
from trac.versioncontrol.cache import CachedRepository
from trac.wiki.model import WikiPage

from tracbacklink.api import (TracBackLinkChangeset as Changeset,
                              TracBackLinkSystem)


class TracBackLinkCommandProvider(Component):

    implements(IAdminCommandProvider)

    # IAdminCommandProvider methods

    def get_admin_commands(self):
        yield ('backlink sync', '[realm [id...]]',
               'Synchronize backlink table with several resources',
               None, self._do_sync)

    # Internal methods

    def _do_sync(self, *args):
        if args:
            realm = args[0]
            args = args[1:]
        else:
            realm = None
        if realm == 'ticket':
            args = tuple(int(arg) for arg in args)

        links = {}
        for date, author, source, ref in self._gather_links(realm, args):
            key = (source, ref)
            if key not in links or date < links[key][0]:
                links[key] = (date, author)

        mod = TracBackLinkSystem(self.env)
        with self.env.db_transaction as db:
            if args:
                db("""\
                    DELETE FROM backlink
                    WHERE src_realm=%%s AND src_id IN (%(ids)s) OR
                          src_parent_realm=%%s AND src_parent_id IN (%(ids)s)
                    """ % {'ids': ','.join(('%s',) * len(args))},
                    ((realm,) + args) * 2)
            elif realm:
                db("""\
                    DELETE FROM backlink
                    WHERE src_realm=%s OR src_parent_realm=%s
                    """, (realm, realm))
            else:
                db("DELETE FROM backlink")
                db.update_sequence(None, 'backlink', 'id')
            for (source, ref), (date, author) in links.iteritems():
                mod.add_backlink(date, author, source, ref)

    def _gather_links(self, realm, args):
        out = sys.stderr
        isatty = hasattr(out, 'fileno') and os.isatty(out.fileno())

        def print_stat(n_links, n_models, realm, newline=True):
            if isatty:
                msg = 'Gathered %d links from %d %s objects%s' % \
                      (n_links, n_models, realm, '' if newline else '\r')
                console_print(out, msg, newline=newline)

        mod = TracBackLinkSystem(self.env)
        specs = [
            ('wiki',      self._iter_wikis, mod.gather_links_from_wiki),
            ('ticket',    self._iter_tickets, mod.gather_links_from_ticket),
            ('milestone', self._iter_milestones,
                          mod.gather_links_from_milestone),
            ('changeset', self._iter_changesets,
                          mod.gather_links_from_changeset),
        ]
        for realm_, iter_, gather in specs:
            if realm not in (None, realm_):
                continue
            n_models = n_links = 0
            for model in iter_(args):
                n = 0
                for link in gather(model):
                    yield link
                    n += 1
                n_links += n
                n_models += 1
                print_stat(n_links, n_models, realm_, newline=False)
            print_stat(n_links, n_models, realm_)

    def _iter_wikis(self, args):
        if not args:
            query = 'SELECT DISTINCT name FROM wiki'
            query_args = ()
        else:
            query = 'SELECT DISTINCT name FROM wiki WHERE name IN (%s)' % \
                    (('%s',) * len(args))
            query_args = args
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute(query, query_args)
            for row in cursor:
                try:
                    page = WikiPage(self.env, row[0])
                except ResourceNotFound:
                    continue
                yield page

    def _iter_tickets(self, args):
        if not args:
            query = 'SELECT id FROM ticket ORDER BY id'
            query_args = ()
        else:
            query = 'SELECT id FROM ticket WHERE id IN (%s) ORDER BY id' % \
                    (('%s',) * len(args))
            query_args = args
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute(query, query_args)
            for row in cursor:
                try:
                    ticket = Ticket(self.env, row[0])
                except ResourceNotFound:
                    continue
                yield ticket

    def _iter_milestones(self, args):
        if not args:
            query = 'SELECT name FROM milestone'
            query_args = ()
        else:
            query = 'SELECT name FROM milestone WHERE name IN (%s)' % \
                    (('%s',) * len(args))
            query_args = args
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute(query, query_args)
            for row in cursor:
                try:
                    milestone = Milestone(self.env, row[0])
                except ResourceNotFound:
                    continue
                yield milestone

    def _iter_changesets(self, args):
        if not args or any(arg == '*' for arg in args):
            match_repos = lambda name: True
        else:
            args = set(args)
            match_repos = lambda name: name in args
        manager = RepositoryManager(self.env)
        for reponame in manager.get_all_repositories():
            if not match_repos(reponame):
                continue
            try:
                repos = manager.get_repository(reponame)
            except TracError, e:
                self.log.warning('Exception caught from RepositoryManager.'
                                 'get_repository(%r): %s',
                                 reponame, exception_to_unicode(e))
                continue
            iter_csets = self._iter_cached_csets \
                         if isinstance(repos, CachedRepository) else \
                         self._iter_normal_csets
            for cset in iter_csets(repos):
                yield cset

    def _iter_cached_csets(self, repos):
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute("""\
                SELECT rev, time, author, message FROM revision
                WHERE repos=%s
                """, (repos.id,))
            for rev, date, author, message in cursor:
                yield Changeset(repos, rev, message, author,
                                from_utimestamp(date))

    def _iter_normal_csets(self, repos):
        try:
            node = repos.get_node('')
        except Exception, e:
            self.log.warning('Exception caught from %s.get_node("") for '
                             'repository "%s": %s',
                             repos.__class__.__name__, repos.reponame,
                             exception_to_unicode(e))
        for path, rev, change in node.get_history():
            try:
                cset = repos.get_changeset(rev)
            except Exception, e:
                self.log.warning('Exception caught from %s.get_changeset() '
                                 'for repository "%s": %s',
                                 repos.__class__.__name__, repos.reponame,
                                 exception_to_unicode(e))
            else:
                yield cset
