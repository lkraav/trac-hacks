# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2013 Daniel Atallah <datallah@pidgin.im>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.attachment import IAttachmentChangeListener
from trac.config import Option
from trac.core import *
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.util import get_reporter_id
from trac.util.datefmt import utc


class RemovePendingPlugin(Component):

    implements(IAttachmentChangeListener, ITicketManipulator)

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

                # Trigger notification since we've changed the ticket.
                tn = TicketNotifyEmail(self.env)
                tn.notify(ticket, newticket=False, modtime=attachment.date)

    def attachment_deleted(self, attachment):
        pass
