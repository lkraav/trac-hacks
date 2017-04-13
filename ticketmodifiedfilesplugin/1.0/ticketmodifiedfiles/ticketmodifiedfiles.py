# -*- coding: utf-8 -*-
#
# This software is licensed as described in the file COPYING.txt, which you
# should have received as part of this distribution.

import re

from trac.config import ListOption
from trac.core import Component, implements
from trac.resource import ResourceNotFound
from trac.ticket.model import Ticket
from trac.util import as_int
from trac.versioncontrol.api import NoSuchChangeset, NoSuchNode, \
                                    RepositoryManager
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_script, \
                            add_stylesheet, add_warning
from trac.util.datefmt import format_time
from trac.util.html import html as tag
from trac.util.translation import _, ngettext


class TicketModifiedFilesPlugin(Component):
    implements(IRequestHandler, IRequestFilter, ITemplateProvider)

    ignored_statuses = ListOption('modifiedfiles', 'ignored_statuses',
        default='closed',
        doc="""Statuses to ignore when looking for conflicting tickets.""")

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/modifiedfiles/([0-9]+)$', req.path_info)
        if match:
            req.args['id'] = match.group(1)
            return True

    def process_request(self, req):
        # Retrieve information needed to display in the /modifiedfiles/ page
        (id_, files, deletedfiles, ticketsperfile, filestatus,
         conflictingtickets, ticketisclosed, revisions,
         ticketsdescription) = self._process_ticket_request(req)

        data = {
            'ticketid': id_,
            'files': files,
            'deletedfiles': deletedfiles,
            'ticketsperfile': ticketsperfile,
            'filestatus': filestatus,
            'conflictingtickets': conflictingtickets,
            'ticketisclosed': ticketisclosed,
            'revisions': revisions,
            'ticketsdescription': ticketsdescription
        }

        add_ctxtnav(req, _("Back to Ticket #%(id)s", id=id_),
                    req.href.ticket(id_))
        add_stylesheet(req, 'common/css/diff.css')
        add_stylesheet(req, 'tmf/css/ticketmodifiedfiles.css')
        add_script(req, 'tmf/js/ticketmodifiedfiles.js')

        return 'ticketmodifiedfiles.html', data, None

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            numconflictingtickets = self._process_ticket_request(req, True)
            # Display a warning message if there are conflicting tickets
            if numconflictingtickets > 0:
                add_warning(req, ngettext(
                    "There is %(n)s other ticket which change the same files",
                    "There are %(n)s tickets which change the same files",
                    numconflictingtickets, n=numconflictingtickets))
            add_ctxtnav(req, tag.a("Modified Files",
                                   href=req.href.modifiedfiles(
                                       req.args.get('id'))))
        return template, data, content_type

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tmf', resource_filename(__name__, 'htdocs'))]

    # Internal methods

    def _process_ticket_request(self, req, justnumconflictingtickets=False):
        id_ = as_int(req.args.get('id'), None)
        req.perm('ticket', id_).require('TICKET_VIEW')

        # Check if the ticket exists (throws an exception if the ticket
        # does not exist)
        this_ticket = Ticket(self.env, id_)

        # Tickets that are in the ignored states can not be in conflict
        if justnumconflictingtickets and \
                this_ticket['status'] in self.ignored_statuses:
            return 0

        files = []
        revisions = []
        tickets_per_file = {}

        rm = RepositoryManager(self.env)
        repositories = {}
        # Retrieve all the revisions which's messages contain "#<TICKETID>"
        with self.env.db_query as db:
            for repos_name, rev, time, author, message in db("""
                    SELECT rep.value, rev.rev, rev.time, rev.author, rev.message 
                    FROM revision AS rev
                     LEFT OUTER JOIN repository AS rep 
                      ON rep.id=rev.repos AND rep.name='name'
                    WHERE rev.message %s
                    """ % db.like(), ('%' + '#%s' % id_ + '%',)):
                # Filter out non-related revisions.
                # for instance, you are lookink for #19, so you don't want
                # #190, #191, #192, etc. to interfere
                # To filter, check what the eventual char after "#19" is.
                # If it's a number, we dont' want it (validrevision = False),
                # but if it's text, keep this revision
                valid_revision = True
                tempstr = message.split("#%s" % id_, 1)
                if len(tempstr[1]) > 0 and \
                        isinstance(as_int(tempstr[1][0], None), int):
                    valid_revision = False

                if valid_revision:
                    if not justnumconflictingtickets:
                        date = '(%s)' % format_time(time, '%d/%m/%Y - %H:%M')
                        revisions.append((rev, author, date))
                    if repos_name in repositories:
                        repos = repositories.get(repos_name)
                    else:
                        repos = rm.get_repository(repos_name)
                        repositories[repos_name] = repos
                    try:
                        changeset = repos.get_changeset(rev)
                    except NoSuchChangeset:
                        pass
                    else:
                        for node_change in changeset.get_changes():
                            files.append((repos, node_change[0]))

        file_status = {}

        for repos, file_ in files:
            # Get the last status of each file
            if not justnumconflictingtickets:
                try:
                    node = repos.get_node(file_)
                except NoSuchNode:
                    # If the node doesn't exist (in the last revision) it
                    # means that it has been deleted
                    file_status[file_] = "delete"
                else:
                    file_status[file_] = node.get_history().next()[2]

            # Get the list of conflicting tickets per file
            temp_tickets_list = []
            for message, in self.env.db_query("""
                    SELECT message FROM revision 
                    WHERE rev IN (SELECT rev FROM node_change 
                                  WHERE path=%s AND repos=%s)
                    """, (file_, repos.id)):
                # Extract the ticket number
                match = re.search(r'#([0-9]+)', message)
                if match:
                    ticket = int(match.group(1))
                    # Don't add yourself
                    if ticket != id_:
                        temp_tickets_list.append(ticket)
            temp_tickets_list = self._remove_duplicated_elements_and_sort(
                temp_tickets_list)

            tickets_per_file[file_] = []
            # Keep only the active tickets
            for ticket in temp_tickets_list:
                try:
                    if Ticket(self.env, ticket)['status'] \
                            not in self.ignored_statuses:
                        tickets_per_file[file_].append(ticket)
                except ResourceNotFound:
                    pass

        # Get the global list of conflicting tickets
        # Only if the ticket is not already closed
        conflicting_tickets = []
        tickets_description = {id_: this_ticket['summary']}
        ticket_is_closed = True
        if this_ticket['status'] not in self.ignored_statuses:
            ticket_is_closed = False
            for fn, relticketids in tickets_per_file.items():
                for relticketid in relticketids:
                    tick = Ticket(self.env, relticketid)
                    conflicting_tickets.append(
                        (relticketid, tick['status'], tick['owner']))
                    tickets_description[relticketid] = tick['summary']

            # Remove duplicated values
            conflicting_tickets = \
                self._remove_duplicated_elements_and_sort(conflicting_tickets)

        # Return only the number of conflicting tickets (if asked for)
        if justnumconflictingtickets:
            return len(conflicting_tickets)

        # Separate the deleted files from the others
        deleted_files = set()
        for repos, file_ in files:
            if file_status[file_] == "delete":
                deleted_files.add(file_)
        for repos, deleted_file in deleted_files:
            files.remove((repos, deleted_file))

        files = sorted(set(file_[1] for file_ in files))

        # Return all the needed information
        return (id_, files, deleted_files, tickets_per_file, file_status,
                conflicting_tickets, ticket_is_closed, revisions,
                tickets_description)

    def _remove_duplicated_elements_and_sort(self, list_):
        d = {}
        for x in list_:
            d[x] = 1
        return sorted(d.keys())
