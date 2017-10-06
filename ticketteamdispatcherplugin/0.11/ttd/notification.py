# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Alexander von Bremen-Kuehne
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.ticket.notification import TicketNotifyEmail

from tracusermanager.api import UserManager


class SpecialTicketNotifyEmail(TicketNotifyEmail):
    """Special Notification of ticket changes."""
    _team = None

    def notify(self, ticket, newticket=True, modtime=None):
        self._team = ticket['ttd']
        if self._team is not None:
            super(SpecialTicketNotifyEmail, self) \
                .notify(ticket, newticket, modtime)
        else:
            self.env.log.warning("Ticket has no custom field called 'ttd'!")

    def get_recipients(self, tktid):
        recipients = []
        for user in UserManager(self.env).get_active_users():
            if user[self._team] == '1':
                recipients.append(user['email'])
        return recipients, []
