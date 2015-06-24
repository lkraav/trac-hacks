# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import functools
from subprocess import Popen, STDOUT, PIPE

from genshi.builder import tag
from trac.core import *
from trac.config import ListOption, Option
from trac.resource import Resource
from trac.util.datefmt import format_datetime, to_utimestamp, user_time
from trac.versioncontrol.api import IRepositoryChangeListener, RepositoryManager
from trac.versioncontrol.web_ui.changeset import ChangesetModule
from trac.web.chrome import (ITemplateProvider, add_script, add_script_data,
    add_stylesheet, pretty_timedelta, web_context)
from trac.web.href import Href
from trac.web.main import IRequestFilter
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase
from trac.ticket.model import Ticket
from tracopt.ticket.commit_updater import CommitTicketUpdater

from model import CodeReview
from api import is_incomplete

class CodeReviewerModule(Component):
    """Base component for reviewing changesets."""

    implements(ITemplateProvider, IRequestFilter)

    # config options
    statuses = ListOption('codereviewer', 'status_choices',
        default=CodeReview.STATUSES, doc="Review status choices.")

    passed = ListOption('codereviewer', 'passed',
        default=[], doc="Ticket field changes on a PASSED submit.")

    failed = ListOption('codereviewer', 'failed',
        default=[], doc="Ticket field changes on a FAILED submit.")

    completeness = ListOption('codereviewer', 'completeness',
        default=[], doc="Ticket field values that enable ticket completeness.")

    command = Option('codereviewer', 'command',
        default='', doc="Command to execute upon ticket completeness.")

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('coderev', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/changeset'):
            changeset = data['changeset']
            repos, rev = changeset.repos.reponame, changeset.rev
            review = CodeReview(self.env, repos, rev)
            tickets = req.args.getlist('tickets')
            if req.method == 'POST':
                status_changed = \
                    review.encode(req.args['status']) != review.status
                if review.save(req.authname, req.args['status'],
                               req.args['summary']):
                    self._update_tickets(review, status_changed)
                    tickets = review.tickets
                href = Href(req.path_info)
                req.redirect(href(tickets=tickets))
            ctx = web_context(req)
            format_summary = functools.partial(format_to_html, self.env, ctx,
                                               escape_newlines=True)
            format_time = functools.partial(user_time, req, format_datetime)

            add_stylesheet(req, 'coderev/coderev.css')
            add_script(req, 'coderev/coderev.js')
            add_script_data(req, {
                'review': {
                    'status': review.status,
                    'encoded_status': review.encode(review.status),
                    'summaries': [
                        dict([
                            ('html_summary', format_summary(r['summary'])),
                            ('pretty_when', format_time(r['when'])),
                            ('pretty_timedelta', pretty_timedelta(r['when'])),
                            ('reviewer', r['reviewer']),
                            ('status', r['status'])
                        ]) for r in CodeReview.select(self.env, repos, rev)
                    ],
                },
                'tickets': tickets,
                'statuses': self.statuses,
                'form_token': req.form_token,
            })
            req.send_header('Cache-Control', 'no-cache')
        elif req.path_info.startswith('/ticket/'):
            add_stylesheet(req, 'coderev/coderev.css')
        return template, data, content_type

    # Private methods

    def _update_tickets(self, review, status_changed):
        """Updates the tickets referenced by the given review's changeset
        with a comment of field changes.  Field changes and command execution
        may occur if specified in trac.ini and the review's changeset is the
        last one of the ticket."""
        status = review.encode(review.status).lower()

        # build comment
        comment = None
        if status_changed or review['summary']:
            if status_changed:
                comment = "Code review set to %s" % review['status']
            else:
                comment = "Code review comment"
            repos = RepositoryManager(self.env).get_repository(review.repo)
            ref = review.changeset
            disp_ref = repos.short_rev(review.changeset)
            if review.repo:
                ref += '/' + review.repo
                disp_ref += '/' + review.repo
            comment += ' for [changeset:"%s" %s]' % (ref, disp_ref)
            if review['summary']:
                comment += ":\n\n%s" % review['summary']

        invoked = False
        for ticket in review.tickets:
            tkt = Ticket(self.env, ticket)

            # determine ticket changes
            changes = {}
            if self._is_complete(ticket, review, failed_ok=True):
                changes = self._get_ticket_changes(tkt, status)

            # update ticket if there's a review summary or ticket changes
            if comment or changes:
                for field, value in changes.items():
                    tkt[field] = value
                tkt.save_changes(review['reviewer'], comment)

            # check to invoke command
            if not invoked and self._is_complete(ticket, review):
                self._execute_command()
                invoked = True

    def _is_complete(self, ticket, review, failed_ok=False):
        """Returns True if the ticket is complete (or only the last review
        failed if ok_failed is True) and therefore actions (e.g., ticket
        changes and executing commands) should be taken.

        A ticket is complete when its completeness criteria is met and
        the review has PASSED and is the ticket's last review with no
        other PENDING reviews.  Completeness criteria is defined in
        trac.ini like this:

         completeness = phase=(codereview|verifying|releasing)

        The above means that the ticket's phase field must have a value
        of either codereview, verifying, or releasing for the ticket to
        be considered complete.  This helps prevent actions from being
        taken if there's a code review of partial work before the ticket
        is really ready to be fully tested and released.
        """
        # check review's completeness
        reason = is_incomplete(self.env, review, ticket)
        if failed_ok and reason and CodeReview.NOT_PASSED in reason:
            return True
        return not reason

    def _get_ticket_changes(self, tkt, status):
        """Return a dict of field-value pairs of ticket fields to change
        for the given ticket as defined in trac.ini.  As one workflow
        opinion, the changes are processed in order:

         passed = phase=verifying,owner={captain}

        In the above example, if the review passed and the ticket's phase
        already = verifying, then the owner change will not be included.
        """
        changes = {}
        for group in getattr(self, status, []):
            field, value = group.split('=', 1)
            if value.startswith('{'):
                value = tkt[value.strip('{}')]
            if tkt[field] == value:
                break  # no more changes once ticket already has target value
            changes[field] = value
        return changes

    def _execute_command(self):
        if not self.command:
            return
        p = Popen(self.command, shell=True, stderr=STDOUT, stdout=PIPE)
        out = p.communicate()[0]
        if p.returncode == 0:
            self.log.info('command: %s' % self.command)
        else:
            self.log.error('command error: %s\n%s' % (self.command, out))


class CommitTicketReferenceMacro(WikiMacroBase):
    """This is intended to replace the builtin macro by providing additional
    code review status info for the changeset.  To use, disable the builtin
    macro as follows:

    [components]
    tracopt.ticket.commit_updater.committicketreferencemacro = disabled
    """

    def expand_macro(self, formatter, name, content, args={}):
        reponame = args.get('repository') or ''
        rev_str = args.get('revision')
        repos = RepositoryManager(self.env).get_repository(reponame)
        try:
            changeset = repos.get_changeset(repos.normalize_rev(rev_str))
            message = changeset.message
            rev = changeset.rev
            resource = repos.resource

            # add review status to commit message (
            review = CodeReview(self.env, reponame, rev)
            status = review.encode(review.status)
            message += '\n\n{{{#!html \n'
            message += '<div class="codereviewstatus">'
            message += '  <div class="system-message %s">' % status.lower()
            message += '    <p>Code review status: '
            message += '      <span>%s</span>' % review.status
            message += '    </p>'
            message += '  </div>'
            message += '</div>'
            message += '\n}}}'

        except Exception:
            message = content
            resource = Resource('repository', reponame)
        if formatter.context.resource.realm == 'ticket':
            ticket_re = CommitTicketUpdater.ticket_re
            if not any(int(tkt_id) == int(formatter.context.resource.id)
                       for tkt_id in ticket_re.findall(message)):
                return tag.p("(The changeset message doesn't reference this "
                             "ticket)", class_='hint')
        if ChangesetModule(self.env).wiki_format_messages:
            ctxt = formatter.context
            return tag.div(format_to_html(self.env, ctxt('changeset', rev,
                                                         parent=resource),
                                          message, escape_newlines=True),
                           class_='message')
        else:
            return tag.pre(message, class_='message')


class ChangesetTicketMapper(Component):
    """Maintains a mapping of changesets to tickets in a codereviewer_map
    table. Invoked for each changeset addition or modification."""

    implements(IRepositoryChangeListener)

    # IRepositoryChangeListener methods

    def changeset_added(self, repos, changeset):
        self._map(repos.reponame, changeset)

    def changeset_modified(self, repos, changeset, old_changeset):
        self._map(repos.reponame, changeset, update=True)

    # Internal methods

    def _map(self, reponame, changeset, update=False):
        # Extract tickets from changeset message.
        ctu = CommitTicketUpdater(self.env)
        tickets = set(ctu._parse_message(changeset.message))
        when = to_utimestamp(changeset.date)

        with self.env.db_transaction as db:
            if update:
                db("""DELETE FROM codereviewer_map
                   WHERE repo=%s and changeset=%s
                   """, (reponame or '', changeset.rev))
            if not tickets:
                tickets = ['']  # we still want merges inserted
            for ticket in tickets:
                try:
                    db("""INSERT INTO codereviewer_map
                        (repo,changeset,ticket,time)
                       VALUES (%s,%s,%s,%s)
                       """, (reponame or '', changeset.rev, ticket, when))
                except Exception, e:
                    self.log.warning("Unable to insert changeset "
                                     "%s/%s and ticket %s into db: %s",
                                     changeset.rev, reponame or '',
                                     ticket, e)
