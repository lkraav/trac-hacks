# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 OpenGroove,Inc.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from __future__ import with_statement

from StringIO import StringIO
import pkg_resources
import re

try:
    from babel.core import Locale
except ImportError:
    Locale = locale_en = None
else:
    locale_en = Locale.parse('en_US')

from trac.attachment import IAttachmentChangeListener
from trac.core import Component, ExtensionPoint, Interface, TracError, \
                      implements
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.resource import Resource, ResourceNotFound, ResourceSystem
from trac.test import Mock, MockPerm
from trac.ticket.api import IMilestoneChangeListener, ITicketChangeListener, \
                            TicketSystem
from trac.ticket.model import Ticket
from trac.util import lazy
from trac.util.datefmt import to_utimestamp, utc
from trac.util.translation import domain_functions
from trac.versioncontrol.api import Changeset, IRepositoryChangeListener, \
                                    RepositoryManager
from trac.versioncontrol.cache import CachedChangeset, CachedRepository
from trac.versioncontrol.web_ui.changeset import ChangesetModule
from trac.web.api import Request, arg_list_to_args
from trac.web.chrome import web_context
from trac.web.session import Session
from trac.wiki.api import IWikiChangeListener, WikiSystem
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage
from trac.wiki.parser import WikiParser

from tracbacklink import db_default


__all__ = ('IBackLinkGatherer',)


_, add_domain = domain_functions('tracbacklink', '_', 'add_domain')


class IBackLinkGatherer(Interface):

    def gather_resources(target):
        """Return a list of Resource instances or an iterable."""


class TracBackLinkSystem(Component):

    implements(IEnvironmentSetupParticipant, IAttachmentChangeListener,
               IWikiChangeListener, ITicketChangeListener,
               IMilestoneChangeListener, IRepositoryChangeListener)

    _gatherers = ExtensionPoint(IBackLinkGatherer)

    def __init__(self):
        try:
            locale_dir = pkg_resources.resource_filename(__name__, 'locale')
        except KeyError:
            pass
        else:
            add_domain(self.env.path, locale_dir)

    # Public methods

    def gather_links_from_attachment(self, attachment):
        time = attachment.date
        author = attachment.author
        resource = attachment.resource
        for ref in gather_links(self.env, attachment, attachment.description):
            yield time, author, resource, ref

    def gather_links_from_wiki(self, page, comments=True):
        time = page.time
        author = page.author
        resource = page.resource

        for ref in gather_links(self.env, page, page.text):
            yield time, author, resource, ref
        if comments:
            with self.env.db_query as db:
                cursor = db.cursor()
                cursor.execute("""\
                    SELECT comment, version FROM wiki
                    WHERE name=%s AND comment!='' ORDER BY version
                    """, (page.name,))
                for comment, version in cursor:
                    for ref in gather_links(self.env, page, comment):
                        resource = page.resource.child('comment', version)
                        yield time, author, resource, ref
        else:
            for ref in gather_links(self.env, page, page.comment):
                resource = page.resource.child('comment', page.version)
                yield time, author, resource, ref
        for ref in self._gather_from_extpoints(page):
            yield time, author, resource, ref

    def gather_links_from_ticket(self, ticket):
        changetime = ticket['changetime']
        reporter = ticket['reporter']
        resource = ticket.resource
        for ref in gather_links(self.env, ticket, ticket['description']):
            yield changetime, reporter, resource, ref
        for field in self._ticket_fields_with_wiki:
            for ref in gather_links(self.env, ticket, ticket[field]):
                yield changetime, reporter, resource, ref
        changelog = ticket.get_changelog()
        for date, author, field, old, new, permanent in changelog:
            if field != 'comment':
                continue
            if old:
                cnum = old.split('.')[-1]
                comment_resource = Resource('comment', cnum, parent=resource)
            else:
                comment_resource = resource
            for ref in gather_links(self.env, ticket, new):
                yield changetime, author, comment_resource, ref
        for ref in self._gather_from_extpoints(ticket):
            yield changetime, author, resource, ref

    def gather_links_from_milestone(self, milestone):
        resource = milestone.resource
        time = milestone.completed or milestone.due
        for ref in gather_links(self.env, milestone, milestone.description):
            yield time, None, resource, ref
        for ref in self._gather_from_extpoints(milestone):
            yield time, None, resource, ref

    def gather_links_from_changeset(self, changeset):
        date = changeset.date
        author = changeset.author
        resource = changeset.resource
        repos = changeset.repos
        if isinstance(repos, CachedRepository):
            resource = repos.resource.child(resource.realm,
                                            repos.db_rev(resource.id))
        for ref in gather_links(self.env, changeset, changeset.message):
            yield date, author, resource, ref
        for ref in self._gather_from_extpoints(changeset):
            yield date, author, resource, ref

    def add_backlink(self, date, author, source, ref):
        args = [date and to_utimestamp(date), author]
        args.extend(_ref_to_args(ref))
        args.extend(_source_to_args(source))
        self.env.db_transaction("""\
            INSERT INTO backlink (
                time, author,
                ref_realm, ref_id, ref_parent_realm, ref_parent_id,
                src_realm, src_id, src_parent_realm, src_parent_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, args)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self._create_schema()

    def environment_needs_upgrade(self, db):
        if 'backlink' not in db.get_table_names():
            return True
        columns = db.get_column_names('backlink')
        for table in db_default.schema:
            if table.name == 'backlink':
                if set(c.name for c in table.columns) != set(columns):
                    return True

    def upgrade_environment(self, db):
        self._create_schema()

    # IAttachmentChangeListener methods

    def attachment_added(self, attachment):
        self._invoke('attachment_added', self._attachment_added, attachment)

    def attachment_deleted(self, attachment):
        self._invoke('attachment_deleted', self._attachment_deleted,
                     attachment)

    def attachment_reparented(self, attachment, old_parent_realm,
                              old_parent_id):
        self._invoke('attachment_reparented', self._attachment_reparented,
                     attachment, old_parent_realm, old_parent_id)

    # IWikiChangeListener methods

    def wiki_page_added(self, page):
        self._invoke('wiki_page_added', self._wiki_added, page)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self._invoke('wiki_page_changed', self._wiki_changed, page)

    def wiki_page_deleted(self, page):
        self._invoke('wiki_page_deleted', self._wiki_deleted, page)

    def wiki_page_version_deleted(self, page):
        self._invoke('wiki_page_version_deleted', self._wiki_changed, page)

    def wiki_page_renamed(self, page, old_name):
        self._invoke('wiki_page_renamed', self._wiki_renamed, page, old_name)

    # ITicketChangeListener methods

    def ticket_created(self, ticket):
        self._invoke('ticket_created', self._ticket_created, ticket)

    def ticket_changed(self, ticket, comment, author, old_values):
        self._invoke('ticket_changed', self._ticket_changed, ticket)

    def ticket_deleted(self, ticket):
        self._invoke('ticket_deleted', self._ticket_deleted, ticket)

    def ticket_comment_modified(self, ticket, cdate, author, comment,
                                old_comment):
        self._invoke('ticket_comment_modified', self._ticket_comment_modified,
                     ticket, cdate, author, comment)

    def ticket_change_deleted(self, ticket, cdate, changes):
        self._invoke('ticket_change_deleted', self._ticket_changed, ticket)

    # IMilestoneChangeListener methods

    def milestone_created(self, milestone):
        self._invoke('milestone_created', self._milestone_created, milestone)

    def milestone_changed(self, milestone, old_values):
        self._invoke('milestone_changed', self._milestone_changed, milestone)

    def milestone_deleted(self, milestone):
        self._invoke('milestone_deleted', self._milestone_deleted, milestone)

    # IRepositoryChangeListener methods

    def changeset_added(self, repos, changeset):
        self._invoke('changeset_added', self._changeset_added, repos,
                     changeset)

    def changeset_modified(self, repos, changeset, old_changeset):
        self._invoke('changeset_modified', self._changeset_modified, repos,
                     changeset, old_changeset)

    # Internal methods

    def _create_schema(self):
        dbm = DatabaseManager(self.env)
        fixup_table = lambda table: table
        if dbm.connection_uri.startswith('mysql://'):
            fixup_table = self._fixup_table_mysql
        connector, args = dbm.get_connector()
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for table in db_default.schema:
                table = fixup_table(table)
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)

    def _fixup_table_mysql(self, table):
        if table.name == 'backlink':
            import copy
            table = copy.deepcopy(table)
            for column in table.columns:
                if column.size and column.type == 'text':
                    column.type = 'VARCHAR(%d)' % column.size
        return table

    def _gather_from_extpoints(self, target):
        for gatherer in self._gatherers:
            for ref in gatherer.gather_resources(target):
                yield ref

    def _invoke(self, name, f, *args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            self.log.warning('Exception caught while "%s"' % name,
                             exc_info=True)

    def _attachment_added(self, attachment):
        self._resource_added(self.gather_links_from_attachment(attachment))

    def _attachment_deleted(self, attachment):
        self._resource_deleted('attachment', attachment.filename,
                               attachment.parent_realm, attachment.parent_id)

    def _attachment_reparented(self, attachment, old_parent_realm,
                               old_parent_id):
        with self.env.db_transaction:
            self._resource_deleted('attachment', None, old_parent_realm,
                                   old_parent_id)
            self._attachment_added(attachment)

    def _wiki_added(self, page):
        self._resource_added(self.gather_links_from_wiki(page))

    def _wiki_changed(self, page):
        with self.env.db_transaction:
            self._wiki_deleted(page)
            self._wiki_added(page)

    def _wiki_renamed(self, page, old_name):
        with self.env.db_transaction:
            try:
                old_page = WikiPage(self.env, old_name)
            except ResourceNotFound:
                pass
            else:
                self._wiki_deleted(old_page)
            self._wiki_added(page)

    def _wiki_deleted(self, page):
        self._resource_deleted('wiki', page.name)

    def _ticket_created(self, ticket):
        self._resource_added(self.gather_links_from_ticket(ticket))

    def _ticket_changed(self, ticket):
        with self.env.db_transaction:
            self._ticket_deleted(ticket)
            self._ticket_created(ticket)

    def _ticket_comment_modified(self, ticket, cdate, author, comment):
        def gather(db):
            for oldvalue, in db("""\
                    SELECT oldvalue FROM ticket_change
                    WHERE ticket=%s AND time=%s AND field='comment' AND
                          oldvalue!=''
                    """, (ticket.id, to_utimestamp(cdate))):
                cnum = oldvalue.split('.')[-1]
                break
            else:
                return
            if cnum.isdigit():
                cnum = int(cnum)
            self._resource_deleted('comment', cnum, 'ticket', ticket.id)
            comment_resource = Resource('comment', cnum,
                                        parent=ticket.resource)
            for ref in gather_links(self.env, ticket, comment):
                yield cdate, author, comment_resource, ref

        with self.env.db_transaction as db:
            self._resource_added(gather(db))

    def _ticket_deleted(self, ticket):
        self._resource_deleted('ticket', ticket.id)

    def _milestone_created(self, milestone):
        self._resource_added(self.gather_links_from_milestone(milestone))

    def _milestone_changed(self, milestone):
        with self.env.db_transaction:
            self._milestone_deleted(milestone)
            self._milestone_created(milestone)

    def _milestone_deleted(self, milestone):
        self._resource_deleted('milestone', milestone.name)

    def _changeset_added(self, repos, changeset):
        self._resource_added(self.gather_links_from_changeset(changeset))

    def _changeset_modified(self, repos, changeset, old_changeset):
        with self.env.db_transaction:
            if isinstance(repos, CachedRepository):
                rev = repos.db_rev(old_changeset.rev)
            self._resource_deleted('changeset', rev, 'repository',
                                   repos.reponame)
            self._changeset_added(repos, changeset)

    def _resource_added(self, gathered):
        args = []
        for date, author, source, ref in gathered:
            arg = [date and to_utimestamp(date), author]
            arg.extend(_ref_to_args(ref))
            arg.extend(_source_to_args(source))
            args.append(arg)
        if not args:
            return
        with self.env.db_transaction as db:
            db.executemany("""\
                INSERT INTO backlink (
                    time, author,
                    ref_realm, ref_id, ref_parent_realm, ref_parent_id,
                    src_realm, src_id, src_parent_realm, src_parent_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, args)

    def _resource_deleted(self, realm, id, parent_realm=False,
                          parent_id=False):
        where = 'src_realm=%s'
        args = [realm]
        if id is not None:
            where += ' AND src_id=%s'
            args.append(_to_u(id))
        if parent_realm is False:
            where += ' OR src_parent_realm=%s AND src_parent_id=%s'
            args.extend(args[:])
        else:
            where += ' AND src_parent_realm=%s AND src_parent_id=%s'
            args.append(parent_realm)
            args.append(_to_u(parent_id))
        query = 'DELETE FROM backlink WHERE ' + where
        self.env.db_transaction(query, args)

    @lazy
    def _ticket_fields_with_wiki(self):
        return [f['name'] for f in TicketSystem(self.env).fields
                          if f['type'] in ('text', 'textarea') and
                             f.get('format') == 'wiki']


class TracBackLinkChangeset(CachedChangeset):

    def __init__(self, repos, rev, message, author, date):
        Changeset.__init__(self, repos, repos.rev_db(rev), message, author,
                           date)


def gather_links(env, source, text):
    if not isinstance(source, Resource):
        source = source.resource
    source = _strip_version(source)
    req = MockRequest(env)
    context = web_context(req, source)
    for ref in LinksGatherer.gather(env, context, text):
        if not _is_equal(source, ref):
            yield ref


def _strip_version(resource):
    if resource and resource.version is not None:
        resource = resource(version=None,
                            parent=_strip_version(resource.parent))
    return resource


def _is_equal(r1, r2):
    return r1 == r2 or r2.parent and r2.parent == r1 or \
            r1.parent and r1.parent == r2


def MockRequest(env, **kwargs):
    authname = 'anonymous'
    perm = MockPerm()

    if 'arg_list' in kwargs:
        arg_list = kwargs['arg_list']
        args = arg_list_to_args(arg_list)
    else:
        args = arg_list_to_args(())
        args.update(kwargs.get('args', {}))
        arg_list = [(name, value) for name in args
                                  for value in args.getlist(name)]

    environ = {
        'trac.base_url': env.abs_href(),
        'wsgi.url_scheme': 'http',
        'HTTP_ACCEPT_LANGUAGE': 'en-US',
        'PATH_INFO': kwargs.get('path_info', '/'),
        'REQUEST_METHOD': kwargs.get('method', 'GET'),
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_USER': authname,
        'SCRIPT_NAME': '/trac.cgi',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
    }

    status_sent = []
    headers_sent = {}
    response_sent = StringIO()

    def start_response(status, headers, exc_info=None):
        status_sent.append(status)
        headers_sent.update(dict(headers))
        return response_sent.write

    req = Mock(Request, environ, start_response)
    req.status_sent = status_sent
    req.headers_sent = headers_sent
    req.response_sent = response_sent

    from trac.web.chrome import Chrome
    req.callbacks.update({
        'arg_list': lambda req: arg_list,
        'args': lambda req: args,
        'authname': lambda req: authname,
        'chrome': Chrome(env).prepare_request,
        'form_token': lambda req: kwargs.get('form_token'),
        'languages': Request._parse_languages,
        'lc_time': lambda req: kwargs.get('lc_time', locale_en),
        'locale': lambda req: kwargs.get('locale'),
        'incookie': Request._parse_cookies,
        'perm': lambda req: perm,
        'session': lambda req: Session(env, req),
        'tz': lambda req: kwargs.get('tz', utc),
        'use_xsendfile': False,
        'xsendfile_header': None,
        '_inheaders': Request._parse_headers,
    })

    return req


def _to_u(value):
    if value is None:
        pass
    elif isinstance(value, str):
        value = unicode(value, 'utf-8')
    elif not isinstance(value, unicode):
        value = unicode(value)
    return value


def _ref_to_args(resource):
    parent = resource.parent
    if parent:
        parent_realm = parent.realm
        parent_id = parent.id
    else:
        parent_realm = parent_id = None
    return [_to_u(value) for value in (resource.realm, resource.id,
                                       parent_realm, parent_id)]


def _source_to_args(resource):
    parent = resource.parent
    if parent:
        parent_realm = parent.realm
        parent_id = parent.id
    else:
        parent_realm = parent_id = None
    return [_to_u(value) for value in (resource.realm, resource.id,
                                       parent_realm, parent_id)]


class LinksGatherer(Formatter):

    @classmethod
    def gather(cls, env, context, text):
        if text:
            gatherer = cls(env, context)
            try:
                gatherer.format(text, NullOut())
                for resource in gatherer.resources:
                    yield resource
            finally:
                gatherer.resources = None

    def __init__(self, env, context):
        self._super = super(LinksGatherer, self)
        Formatter.__init__(self, env, context)
        self.resources = None

    def format(self, text, out=None):
        self.resources = set()
        return self._super.format(text, out)

    @lazy
    def _wiki_name_re(self):
        for pattern, f in WikiSystem(self.env).get_wiki_syntax():
            return re.compile(pattern, re.UNICODE)

    _ticket_re = re.compile(r'#[0-9]+(,[0-9]+)*\Z')

    @lazy
    def _changeset_re(self):
        for pattern, f in ChangesetModule(self.env).get_wiki_syntax():
            return re.compile(pattern, re.UNICODE)

    @lazy
    def _known_realms(self):
        return ResourceSystem(self.env).get_known_realms()

    def handle_match(self, fullmatch):
        for itype, match in fullmatch.groupdict().iteritems():
            if not match or itype in self.wikiparser.helper_patterns:
                continue
            if match[0] == '!':
                return ''
            if self._ticket_re.match(match):
                for num in match[1:].split(','):
                    num = int(num)
                    if Ticket.id_is_valid(num):
                        self._add_resource(Resource('ticket', num))
                return ''
            if self._changeset_re.match(match):
                if match.startswith('r'):
                    self._add_changeset_link(match[1:])
                elif match.startswith('[') and match.endswith(']'):
                    self._add_changeset_link(match[1:-1])
                return ''
            if self._wiki_name_re.match(match):
                self._add_resource(Resource('wiki', match))
                return ''
        return self._super.handle_match(fullmatch)

    def _gather(self, text):
        return self.__class__.gather(self.env, self.context, text)

    def _gather_resources(self, text):
        self.resources.update(self._gather(text))

    def _add_resource(self, resource):
        self.resources.add(resource)

    def _parse_heading(self, match, fullmatch, shorten):
        match = match.strip()
        hdepth = fullmatch.group('hdepth')
        depth = len(hdepth)
        htext = fullmatch.group('htext').strip()
        if htext.endswith(hdepth):
            htext = htext[:-depth]
        self._gather_resources(htext)
        return self._super._parse_heading(match, fullmatch, shorten)

    def _definition_formatter(self, match, fullmatch):
        definition = match[:match.find('::')]
        self._gather_resources(definition)
        return self._super._definition_formatter(match, fullmatch)

    def _macrolink_formatter(self, match, fullmatch):
        macro_or_link = match[2:-2]
        if macro_or_link.startswith('=#'):
            fullmatch = WikiParser._set_anchor_wc_re.match(macro_or_link)
            if fullmatch:
                return self._anchor_formatter(macro_or_link, fullmatch)
        fullmatch = WikiParser._macro_re.match(macro_or_link)
        if fullmatch:
            name = fullmatch.group('macroname')
            args = fullmatch.group('macroargs')
            macrolist = name[-1] == '?'
            if name.lower() == 'br' or name == '?' or macrolist:
                return ''
            if name in ('span', 'Span'):
                self._gather_resources(args)
            return ''
        fullmatch = WikiParser._creolelink_re.match(macro_or_link)
        return self._lhref_formatter(match, fullmatch)

    def close_quote_block(self, escape_newlines):
        if self._quote_buffer:
            if all(not line or line[0] in '> ' for line in self._quote_buffer):
                self._quote_buffer = [line[bool(line and line[0] == ' '):]
                                      for line in self._quote_buffer]
            self._gather_resources(self._quote_buffer)
            self._quote_buffer = []

    def _make_link(self, ns, target, match, label, fullmatch):
        if ns == 'wiki':
            f = self._add_wiki_link
        elif ns == 'ticket':
            f = self._add_ticket_link
        elif ns == 'comment':
            f = self._add_comment_link
        elif ns in ('attachment', 'raw-attachment'):
            f = self._add_attachment_link
        elif ns == 'milestone':
            f = self._add_milestone_link
        elif ns == 'changeset':
            f = self._add_changeset_link
        else:
            return ''
        f(target)
        return ''

    def _add_wiki_link(self, target):
        wikisys = WikiSystem(self.env)
        target = target.rstrip('/') or 'WikiStart'
        referrer = self.resource.id \
                   if self.resource and self.resource.realm == 'wiki' \
                   else ''
        if target.startswith('/'):
            target = target.lstrip('/')
        elif target.startswith(('./', '../')) or target in ('.', '..'):
            target = wikisys._resolve_relative_name(target, referrer)
        else:
            target = wikisys._resolve_scoped_name(target, referrer)
        self._add_resource(Resource('wiki', target))

    def _add_ticket_link(self, target):
        try:
            target = target.encode('utf-8')
        except:
            return
        for id_ in target.split(','):
            try:
                id_ = int(id_)
            except:
                continue
            self._add_resource(Resource('ticket', id_))

    def _add_comment_link(self, target):
        pieces = target.split(':')  # comment:N:ticket:M
        if len(pieces) == 3:
            cnum = pieces[0]
            id_ = pieces[2]
            try:
                cnum = int(cnum)
                id_ = int(id_)
            except:
                pass
            else:
                resource = Resource('comment', cnum,
                                    parent=Resource('ticket', id_))
                self._add_resource(resource)

    def _add_attachment_link(self, target):
        pieces = target.split(':', 2)
        if len(pieces) == 3:
            if pieces[1] in self._known_realms:
                parent_realm = pieces[1]
                parent_id = pieces[2]
                id_ = pieces[0]
            else:
                parent_realm = pieces[0]
                parent_id = pieces[1]
                id_ = pieces[2]
            resource = Resource(parent_realm, parent_id) \
                       .child('attachment', id_)
        else:
            resource = self.resource.child('attachment', target)
        self._add_resource(resource)

    def _add_milestone_link(self, target):
        target = target.strip('/')
        if target:
            self._add_resource(Resource('milestone', target))

    def _add_changeset_link(self, target):
        rm = RepositoryManager(self.env)
        cset, params, fragment = self.split_link(target)
        sep = cset.find('/')
        if sep > 0:
            rev, path = cset[:sep], cset[sep:]
        else:
            rev, path = cset, '/'
        try:
            reponame, repos, path = rm.get_repository_by_path(path)
        except TracError:
            return
        if not repos and not reponame:
            reponame = rm.get_default_repository(self.context)
            if reponame is not None:
                repos = rm.get_repository(reponame)
        if not repos:
            return
        try:
            rev = repos.normalize_rev(rev)
        except TracError:
            return
        if isinstance(repos, CachedRepository):
            rev = repos.db_rev(rev)
        self._add_resource(repos.resource.child('changeset', rev))

    _wiki_processors = set(('div', 'rtl', 'span', 'Span', 'td', 'th', 'tr',
                            'table'))

    def _exec_processor(self, processor, text):
        if processor.name in self._wiki_processors:
            self._gather_resources(text)
        return ''

    def _macro_formatter(self, match, fullmatch, macro, only_inline=False):
        if fullmatch.group('macroname') in self._wiki_processors:
            return self._super._macro_formatter(match, fullmatch, macro,
                                                only_inline=only_inline)
        else:
            return ''


class NullOut(object):

    def write(self, data):
        pass
