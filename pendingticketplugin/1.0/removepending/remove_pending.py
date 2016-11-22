# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2013 Daniel Atallah <datallah@pidgin.im>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from datetime import datetime

from trac.attachment import IAttachmentChangeListener
from trac.config import Option
from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import to_utimestamp, utc


class RemovePendingPlugin(Component):

    implements(ITicketChangeListener, IAttachmentChangeListener)

    pending_removal_status = Option('ticket', 'pending_removal_status', 'new',
        """Status to apply when removing 'Pending' status automatically.""")

    def ticket_created(self, ticket):
        pass

    def ticket_changed(self, ticket, comment, author, old_values):
        # If we're already changing the status, don't do anything else.
        if 'status' not in old_values and author == ticket['reporter'] \
                and ticket['status'] == 'pending':
            self.env.log.info('Removing Pending status for ticket %s due '
                              'to comment', ticket.id)

            new_status = self.config.get('ticket', 'pending_removal_status')

            with self.env.db_transaction as db:
                cursor = db.cursor()

                cursor.execute("""
                    UPDATE ticket SET status = %s
                    WHERE id = %s AND status = %s
                    """, (new_status, ticket.id, 'pending'))

                # Add the ticket change so that it will appear
                # correctly in the history and notifications
                cursor.execute("""
                    INSERT INTO ticket_change
                     (ticket,time,author,field,oldvalue,newvalue)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (ticket.id, to_utimestamp(ticket.time_changed),
                          author, 'status', 'pending', new_status))

    def ticket_deleted(self, ticket):
        pass

    def attachment_added(self, attachment):
        # Check whether we're dealing with a ticket resource
        resource = attachment.resource
        while resource:
            if resource.realm == 'ticket':
                break
            resource = resource.parent

        if resource and resource.realm == 'ticket' \
                and resource.id is not None:
            with self.env.db_transaction as db:
                ticket = Ticket(attachment.env, resource.id, db)
                if attachment.author == ticket['reporter'] and \
                        ticket['status'] == 'pending':
                    self.env.log.info("Removing Pending status for ticket "
                                      "%s due to attachment", ticket.id)

                    comment = "Attachment (%s) added by ticket reporter." \
                              % attachment.filename
                    ticket['status'] = \
                        self.config.get('ticket', 'pending_removal_status')

                    # Determine sequence number.
                    cnum = 0
                    tm = TicketModule(self.env)
                    for change in tm.grouped_changelog_entries(ticket, db):
                        c_cnum = change.get('cnum', None)
                        if c_cnum and int(c_cnum) > cnum:
                            cnum = int(c_cnum)

                    # We can't just use attachment.date as it screws up
                    # event sequencing
                    now = datetime.now(utc)

                    ticket.save_changes(attachment.author, comment, now,
                                        db, str(cnum + 1))

                    # Trigger notification since we've changed the ticket.
                    tn = TicketNotifyEmail(self.env)
                    tn.notify(ticket, newticket=False, modtime=now)

    def attachment_deleted(self, attachment):
        pass
