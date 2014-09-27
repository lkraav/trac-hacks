# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import cgi
import re
import urllib
from pkg_resources import parse_version, resource_filename
try:
    import json
except ImportError:
    import simplejson as json

import trac
from trac.config import IntOption, Option
from trac.core import *
from trac.mimeview.api import Context
from trac.perm import IPermissionRequestor
from trac.versioncontrol.api import RepositoryManager
from trac.web.api import IRequestHandler, ITemplateStreamFilter, RequestDone
from trac.web.chrome import (Chrome, ITemplateProvider, add_script,
                             add_stylesheet)
from trac.wiki.formatter import format_to_oneliner
from trac.util.datefmt import format_datetime
from trac.util.text import shorten_line
try:
    from trac.util.datefmt import from_utimestamp as from_timestamp
except ImportError:
    from trac.util.datefmt import from_timestamp
try:
    from trac.util.datefmt import user_time
except ImportError:
    def user_time(req, func, *args, **kwargs):
        if 'tzinfo' not in kwargs:
            kwargs['tzinfo'] = getattr(req, 'tz', None)
        return func(*args, **kwargs)

from i18n_domain import _, N_, add_domain, gettext, tag_


class TicketlogModule(Component):

    implements(IPermissionRequestor, IRequestHandler, ITemplateProvider,
               ITemplateStreamFilter)

    max_message_length = IntOption('ticketlog', 'log_message_maxlength',
        doc="""Maximum length of log message to display.""")

    log_pattern = Option('ticketlog', 'log_pattern', '\s*#%s[:\s]+.*',
        "Regex to determine which changesets reference the ticket.")

    def __init__(self):
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)
        self.supports_multirepos = parse_version(trac.__version__) >= (0, 12)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TICKETLOG_VIEW', 'TICKETLOG_EDIT', 'TICKETLOG_ADMIN']

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('ticketlog', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/ticketlog')

    def process_request(self, req):
        req.perm.require('TICKETLOG_VIEW')

        if req.path_info.startswith('/ticketlog/query'):
            # query revisions of ticket
            result = {
                'msg_query_err': _("Error in querying changelogs."),
                'msg_tkt_rev_head': _("Commit History"),
                'data': self._handle_ticketlog_query(req),
                'status': '1',
            }
            self._send_response(req, json.dumps(result))

        return 'ticketlog.html', {
            'gettext': gettext,
            '_': _,
            'tag_': tag_,
            'N_': N_,
        }, None

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' \
                and req.path_info.startswith('/ticket/') \
                and 'TICKETLOG_VIEW' in req.perm:
            add_stylesheet(req, 'ticketlog/ticketlog.css')
            add_script(req, 'ticketlog/json2.js')
            add_script(req, 'ticketlog/ticketlog.js')

        return stream

    # Internal methods

    def _handle_ticketlog_query(self, req):
        """handler for query ticket revisions """
        jsonstr = urllib.unquote(req.read())
        req.args.update(json.loads(jsonstr))

        # query ticket revisions
        ticket_id = req.args.get('ticket_id')
        return {
            'ticket_id': ticket_id,
            'headers': [
                _('Changeset'),
                _('Author'),
                _('Time'),
                _('ChangeLog')
            ],
            'header_width': [
                '5em',
                '6em',
                '8em',
                '',
            ],
            'revisions': self._get_ticket_revisions(req, ticket_id),
        }

    def _get_ticket_revisions(self, req, ticket_id):
        """ get ticket revisions """
        revisions = []

        if not ticket_id:
            return revisions

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if self.supports_multirepos:
            cursor.execute("""
                SELECT p.value, v.rev, v.author, v.time, v.message
                  FROM revision v
                  LEFT JOIN repository p
                    ON v.repos = p.id AND p.name='name'
                  WHERE message LIKE %s
            """, ('%#' + ticket_id + '%',))
        else:
            cursor.execute("""
                SELECT rev, author, time, message
                  FROM revision
                  WHERE message LIKE %s
            """, ('%#' + ticket_id + '%',))
            
        rows = cursor.fetchall()

        p = re.compile(self.log_pattern % ticket_id, re.M + re.S + re.U)

        intermediate = {}
        for row in rows:
            if self.supports_multirepos:
                repos_name, rev, author, timestamp, message = row
                repos = RepositoryManager(self.env).get_repository(repos_name)
                rev = repos.normalize_rev(rev)
            else:
                repos_name = None
                rev, author, timestamp, message = row

            if not p.match(message):
                continue

            if self.supports_multirepos:
                link = '%s/%s' % (rev, repos_name)
                # Using (rev, author, time, message) as the key 
                # If branches from the same repo are under Trac system
                # Only one changeset will be in the ticket changelog
                intermediate[(rev, author, timestamp, message)] = link
            else:
                intermediate[(rev, author, timestamp, message)] = rev

        for key in intermediate:
            rev, author, timestamp, message = key
            revision = {
                'rev': rev,
                'author': Chrome(self.env).format_author(req, author),
                'time': user_time(req, format_datetime,
                                  from_timestamp(timestamp)),
            }
            if self.max_message_length \
                    and len(message) > self.max_message_length:
                message = shorten_line(message, self.max_message_length)
            message = cgi.escape(message)
            ctxt = Context.from_request(req)
            revision['message'] = format_to_oneliner(self.env, ctxt, message)
            revision['link'] = intermediate[key]
            revisions.append(revision)

        revisions.sort(key=lambda r: r['time'], reverse=True)

        return revisions

    def _send_response(self, req, message):
        """ send response and stop request handling
        """
        req.send_response(200)
        req.send_header('Cache-control', 'no-cache')
        req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
        req.send_header('Content-Type', 'text/plain' + ';charset=utf-8')
        req.send_header('Content-Length', len(isinstance(message, unicode)
                                          and message.encode('utf-8')
                                          or message))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(message)
        raise RequestDone
