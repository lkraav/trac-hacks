# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import trac.ticket.notification as notification
from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.config import ListOption
from trac.ticket.model import Ticket


class FlexibleReporterNotifyEmail(Component):

    implements(IEnvironmentSetupParticipant)

    notify_states = ListOption('notification','reporter_states', [],
        doc="Ticket states in which the reporter should be notified.")

    def environment_created(self):
      pass

    def environment_needs_upgrade(self, db):
        get_recipients_base = notification.TicketNotifyEmail.get_recipients

        def get_recipients(self, tktid):
            to_recipients, cc_recipients = get_recipients_base(self, tktid)
            notify_states = self.config.get('notification', 'reporter_states')
            ticket = Ticket(self.env, tktid)
            if ticket['status'] not in notify_states and \
                    ticket['reporter'] in to_recipients:
                to_recipients.remove(ticket['reporter'])

            return to_recipients, cc_recipients

        notification.TicketNotifyEmail.get_recipients = get_recipients

    def upgrade_environment(self, db):
      pass
