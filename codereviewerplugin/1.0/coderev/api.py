# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.db.schema import Column, Index, Table
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.resource import ResourceNotFound
from trac.ticket.model import Ticket

import coderev.compat
from coderev.model import get_reviews_for_ticket

DB_NAME = 'coderev'
DB_VERSION = 3

schema = [
    Table('codereviewer')[
        Column('repo', type='text'),
        Column('changeset', type='text'),
        Column('status', type='text'),
        Column('reviewer', type='text'),
        Column('summary', type='text'),
        Column('time', type='int64'),
        Index(['repo', 'changeset', 'time']),
    ],
    Table('codereviewer_map', key=['repo', 'changeset', 'ticket'])[
        Column('repo', type='text'),
        Column('changeset', type='text'),
        Column('ticket', type='text'),
        Column('time', type='int64'),
    ],
]


class CodeReviewerSystem(Component):
    """System management for codereviewer plugin."""

    implements(IEnvironmentSetupParticipant, IPermissionRequestor)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db=None):
        return DatabaseManager(self.env).needs_upgrade(DB_VERSION, DB_NAME)

    def upgrade_environment(self, db=None):
        dbm = DatabaseManager(self.env)
        if dbm.get_database_version(DB_NAME) is False:
            dbm.create_tables(schema)
            dbm.set_database_version(DB_VERSION, DB_NAME)
        else:
            dbm.upgrade(DB_VERSION, DB_NAME, 'coderev.upgrades')

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['CODEREVIEWER_MODIFY']


def is_incomplete(env, review, ticket):
    """Returns False if the ticket is complete - meaning:

     * the ticket satisfies its completeness criteria
     * no reviews are PENDING for this ticket
     * this ticket's last review PASSED

    If the ticket is incomplete, then a string is returned that explains
    the reason.
    """
    # check completeness criteria
    try:
        tkt = Ticket(env, ticket)
    except ResourceNotFound:
        pass  # e.g., incorrect ticket reference
    else:
        for criteria in env.config.getlist('codereviewer', 'completeness'):
            if '=' not in criteria:
                continue
            field, rule = criteria.split('=', 1)
            value = tkt[field]
            rule_re = re.compile(rule)
            if value is None or not rule_re.search(value):
                return "Ticket #%s field %s=%s which violates rule " \
                       "%s" % (tkt.id, field, value, rule)

    # check review status
    reviews = get_reviews_for_ticket(env, ticket)
    if not reviews:
        return "Ticket #%s has no reviews." % ticket
    for review in reviews:
        if review.encode(review.status) == 'PENDING':
            return "Ticket #%s has a %s review for changeset %s" \
                   % (ticket, review. status, review. changeset)
    if review.encode(review.status) != 'PASSED':
        return "Ticket #%s's last changeset %s = %s %s" \
               % (ticket, review. changeset, review. status,
                  review.NOT_PASSED)

    return False
