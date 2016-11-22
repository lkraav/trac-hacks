#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2013 Daniel Atallah <datallah@pidgin.im>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

# Script to close old tickets that are in Pending status.
#
# It should be called via cron on a daily basis to close old tickets:
#
# TRAC_ENV=/somewhere/trac/project/
# DAYS_PENDING=14
#
# /usr/bin/python /path/to/trac_scripts/close_old_pending.py \
#  -p "$TRAC_ENV" -d $DAYS_PENDING

import sys
import traceback
from datetime import datetime, timedelta
from optparse import OptionParser

from trac.env import open_environment
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import utc, to_utimestamp

AUTHOR = 'trac-robot'
MESSAGE = "This ticket was closed automatically by the system. " \
          "It was previously set to a Pending status and hasn't " \
          "been updated within %s days."


parser = OptionParser()
parser.add_option('-p', '--project', dest='project',
                  help='Path to the Trac project.')
parser.add_option('-d', '--daysback', type='int', dest='maxage', default=14,
                  help='Timeout for Pending Tickets to be closed after.')

options, args = parser.parse_args(sys.argv[1:])


class CloseOldPendingTickets(object):

    def __init__(self, project=options.project, author=AUTHOR,
                 maxage=options.maxage):

        msg = MESSAGE % maxage
        now = datetime.now(utc)
        max_time = to_utimestamp(now - timedelta(days=maxage))

        try:
            self.env = open_environment(project)

            with self.env.db_transaction as db:
                for id, in db("""
                        SELECT id FROM ticket
                        WHERE status = %s AND changetime < %s
                        """, ('pending', max_time)):
                    try:
                        ticket = Ticket(self.env, id, db)
                        ticket['status'] = 'closed'
                        ticket.save_changes(author, msg, now)
                        print('Closing Ticket %s (%s)' % (id, ticket['summary']))
                        tn = TicketNotifyEmail(self.env)
                        tn.notify(ticket, newticket=0, modtime=now)
                    except Exception, e:
                        traceback.print_exc(file=sys.stderr)
                        print>>sys.stderr, \
                            'Unexpected error while processing ticket ID %s: %s' \
                            % (id, e)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            print>>sys.stderr, 'Unexpected error while retrieving tickets'


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("For usage: %s --help" % (sys.argv[0]))
    else:
        CloseOldPendingTickets()
