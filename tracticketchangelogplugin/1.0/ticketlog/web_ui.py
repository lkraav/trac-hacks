# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
from pkg_resources import resource_filename

try:
    import json
except ImportError:
    import simplejson as json

from genshi.filters.transform import Transformer
from trac.config import IntOption, Option
from trac.core import Component, implements
from trac.mimeview.api import Context
from trac.resource import Resource
from trac.versioncontrol.api import RepositoryManager
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import Chrome, ITemplateProvider, add_stylesheet
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import format_datetime, from_utimestamp, user_time
from trac.util.text import shorten_line

from i18n_domain import add_domain


class TicketlogModule(Component):
    implements(ITemplateProvider, ITemplateStreamFilter)

    max_message_length = IntOption('ticketlog', 'log_message_maxlength',
        doc="""Maximum length of log message to display.""")

    log_pattern = Option('ticketlog', 'log_pattern', '^\s*#%s[:\s]+.*$',
        "Regex to determine which changesets reference the ticket.")

    def __init__(self):
        try:
            locale_dir = resource_filename(__name__, 'locale')
        except KeyError:
            pass
        else:
            add_domain(self.env.path, locale_dir)

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('ticketlog', resource_filename(__name__, 'htdocs'))]

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html' and \
                req.path_info.startswith('/ticket/'):
            ticket_id = req.args.get('id')
            resource = Resource('ticket', ticket_id)
            if 'LOG_VIEW' in req.perm(resource):
                add_stylesheet(req, 'ticketlog/ticketlog.css')
                revisions = self._get_ticket_revisions(req, ticket_id)
                template = Chrome(self.env)\
                    .load_template('ticketlog.html')\
                    .generate(revisions=revisions)
                stream |= Transformer('//div[@id="ticket"]').after(template)
        return stream

    # Internal methods

    def _get_ticket_revisions(self, req, ticket_id):
        revisions = []

        if not ticket_id:
            return revisions

        p = re.compile(self.log_pattern % ticket_id, re.M + re.U)

        rm = RepositoryManager(self.env)
        intermediate = {}
        for row in self.env.db_query("""
                SELECT p.value, v.rev, v.author, v.time, v.message
                FROM revision v
                  LEFT JOIN repository p ON v.repos = p.id AND p.name='name'
                WHERE message LIKE %s
                """, ('%#' + ticket_id + '%',)):
            repos_name = row[0]
            rev = row[1]
            author = row[2]
            timestamp = row[3]
            message = row[4]

            if not p.search(message):
                continue

            repos = rm.get_repository(repos_name)
            rev = repos.display_rev(rev)
            link = unicode(rev)
            if repos_name:
                link += '/%s' % repos_name
            # Using (rev, author, time, message) as the key
            # If branches from the same repo are under Trac system
            # Only one changeset will be in the ticket changelog
            intermediate[(rev, author, timestamp, message)] = link

        ctxt = Context.from_request(req)
        for key in intermediate:
            rev, author, timestamp, message = key
            if self.max_message_length \
                    and len(message) > self.max_message_length:
                message = shorten_line(message, self.max_message_length)
            rev_link = "[changeset:%s]" % intermediate[key]
            revision = {
                'link': intermediate[key],
                'rev': format_to_oneliner(self.env, ctxt, rev_link),
                'author': Chrome(self.env).format_author(req, author),
                'timestamp': timestamp,
                'time': user_time(req, format_datetime,
                                  from_utimestamp(timestamp)),
                'message': format_to_html(self.env, ctxt, message),
            }
            revisions.append(revision)

        revisions.sort(key=lambda r: r['timestamp'], reverse=True)

        return revisions
