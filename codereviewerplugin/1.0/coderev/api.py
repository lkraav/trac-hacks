# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import Component, implements
from trac.db import Column, Index, Table
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor

from coderev.compat import DatabaseManager

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
