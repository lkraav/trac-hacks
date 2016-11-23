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
from trac.notification.api import NotificationSystem
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketChangeEvent
from trac.util import as_int, get_reporter_id
from trac.util.datefmt import datetime_now, to_utimestamp, utc
from trac.util.text import exception_to_unicode
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
                now = datetime_now(utc)
                ticket.save_changes(attachment.author, when=now)
                self._send_notification(ticket, attachment.author, now)

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
        author = 'trac'
        comment = MESSAGE % maxage
        now = datetime_now(utc)
        max_time = to_utimestamp(now - datetime.timedelta(days=maxage))

        for id, in self.env.db_query("""
                SELECT id FROM ticket
                WHERE status = %s AND changetime < %s
                """, ('pending', max_time)):
            ticket = Ticket(self.env, id)
            ticket['status'] = 'closed'
            ticket.save_changes(author, comment, now)
            self._send_notification(ticket, author, now, comment)

    def _send_notification(self, ticket, author, modtime=None, comment=None):
        event = TicketChangeEvent('changed', ticket, modtime, author, comment)
        try:
            NotificationSystem(self.env).notify(event)
        except Exception as e:
            self.log.error("Failure sending notification on change to "
                           "ticket #%s: %s",
                           ticket.id, exception_to_unicode(e))
