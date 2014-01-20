# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Alexander von Bremen-Kuehne
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener

from notification import SpecialTicketNotifyEmail


class TicketTeamDispatcher(Component):
    implements(ITicketChangeListener)

    def ticket_created(self, ticket):
        mail = SpecialTicketNotifyEmail(self.env)
        mail.notify(ticket)

    def ticket_changed(self, ticket, comment, author, old_values):
        pass

    def ticket_deleted(self, ticket):
        pass 
