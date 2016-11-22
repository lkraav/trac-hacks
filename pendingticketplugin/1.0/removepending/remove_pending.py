# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2013 Daniel Atallah <datallah@pidgin.im>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import datetime

from trac.admin.api import AdminCommandError, IAdminCommandProvider
from trac.attachment import IAttachmentChangeListener
from trac.config import Option
from trac.core import *
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.util import as_int, get_reporter_id
from trac.util.datefmt import to_utimestamp, utc
from trac.util.translation import _

MESSAGE = "This ticket was closed automatically by the system. " \
          "It was previously set to a Pending status and hasn't " \
          "been updated within %s days."


class RemovePendingPlugin(Component):

    implements(IAdminCommandProvider, IAttachmentChangeListener,
               ITicketManipulator)

    pending_removal_status = Option('ticket', 'pending_removal_status', 'new',
        """Status to apply when removing 'Pending' status automatically.""")

    # ITicketManipulator methods

    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        author = get_reporter_id(req, 'author')
        if 'status' not in ticket._old and \
                ticket['reporter'] == author and \
                ticket['status'] == 'pending':
            ticket['status'] = self.pending_removal_status
        return []

    # IAttachmentChangeListener methods

    def attachment_added(self, attachment):
        # Check whether we're dealing with a ticket resource
        resource = attachment.resource
        while resource:
            if resource.realm == 'ticket':
                break
            resource = resource.parent

        if resource and resource.realm == 'ticket' \
                and resource.id is not None:
            ticket = Ticket(self.env, resource.id)
            if ticket['reporter'] == attachment.author and \
                    ticket['status'] == 'pending':
                ticket['status'] = self.pending_removal_status
                ticket.save_changes(attachment.author, when=attachment.date)
                self._send_notification(ticket, attachment.date)

    def attachment_deleted(self, attachment):
        pass

    # AdminCommandProvider methods

    def get_admin_commands(self):
        yield ('ticket close-pending', '<maxage>',
               "Close pending tickets older than <maxage>",
               None, self._close_pending)

    # Private methods

    def _close_pending(self, maxage):
        maxage = as_int(maxage, None)
        if maxage is None:
            raise AdminCommandError(
                _("The argument 'maxage' must be an int."))
        msg = MESSAGE % maxage
        now = datetime.datetime.now(utc)
        max_time = to_utimestamp(now - datetime.timedelta(days=maxage))

        for id, in self.env.db_query("""
                SELECT id FROM ticket
                WHERE status = %s AND changetime < %s
                """, ('pending', max_time)):
            ticket = Ticket(self.env, id)
            ticket['status'] = 'closed'
            ticket.save_changes('trac', msg, now)
            self._send_notification(ticket, now)

    def _send_notification(self, ticket, modtime):
        tn = TicketNotifyEmail(self.env)
        tn.notify(ticket, newticket=False, modtime=modtime)
