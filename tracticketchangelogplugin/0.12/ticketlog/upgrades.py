# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011 Richard Liao <richard.liao.i@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#


"""Automated upgrades for the TracTicketChangelogPlugin database tables, and other data stored
in the Trac environment."""

def add_ticketlog_table(env, db):
    """Migrate db."""
    pass

map = {
    1: [add_ticketlog_table],
}
