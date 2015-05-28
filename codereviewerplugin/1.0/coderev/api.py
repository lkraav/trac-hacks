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
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor

from coderev.compat import DatabaseManager

DB_NAME = 'coderev'
DB_VERSION = 3


class CodeReviewerSystem(Component):
    """System management for codereviewer plugin."""

    implements(IEnvironmentSetupParticipant, IPermissionRequestor)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        return DatabaseManager(self.env).needs_upgrade(DB_VERSION, DB_NAME)

    def upgrade_environment(self, db=None):
        DatabaseManager(self.env).upgrade(DB_VERSION, DB_NAME,
                                          'coderev.upgrades')

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['CODEREVIEWER_MODIFY']
