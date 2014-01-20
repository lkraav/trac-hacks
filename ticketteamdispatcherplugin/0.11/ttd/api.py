# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Alexander von Bremen-Kuehne
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.config import BoolOption
from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener
from datetime import datetime
from trac.util.datefmt import utc

from notification import SpecialTicketNotifyEmail


class TicketTeamDispatcher(Component):
    implements(ITicketChangeListener)

    notify_on_create = BoolOption('team-dispatcher', 'notify_on_create',
                                  True,
                                  doc="Send notification on ticket creation.")

    notify_on_change = BoolOption('team-dispatcher', 'notify_on_change',
                                  False,
                                  doc="Send notification on ticket change.")

    notify_on_delete = BoolOption('team-dispatcher', 'notify_on_delete',
                                  False,
                                  doc="Send notification on ticket deletion.")

    def ticket_created(self, ticket):
        if self.notify_on_create:
            mail = SpecialTicketNotifyEmail(self.env)
            mail.notify(ticket)

    def ticket_changed(self, ticket, comment, author, old_values):
        if self.notify_on_change:
            mail = SpecialTicketNotifyEmail(self.env)
            mail.notify(ticket, False, ticket.values['changetime'])

    def ticket_deleted(self, ticket):
        if self.notify_on_delete:
            now = datetime.now(utc)
            mail = SpecialTicketNotifyEmail(self.env)
            ticket['summary'] += ' (deleted)'
            mail.notify(ticket, False, now)
