# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2012 Colin Guthrie <trac@colin.guthr.ie>
# Copyright (c) 2011-2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.ticket import ITicketChangeListener

from manager import WorkLogManager


class WorkLogTicketObserver(Component):
    implements(ITicketChangeListener)

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        pass

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.

        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        if self.config.getbool('worklog', 'autostop') \
                and 'closed' == ticket['status'] \
                and 'status' in old_values \
                and 'closed' != old_values['status']:
            mgr = WorkLogManager(self.env, self.config)
            who, since = mgr.who_is_working_on(ticket.id)
            if who:
                mgr = WorkLogManager(self.env, self.config, who)
                mgr.stop_work()

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        pass
