# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Rob Guttman <guttman@alum.mit.edu>
# Copyright (C) 2015 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.util.translation import _

DB_NAME = 'coderev'
DB_VERSION = 3


class CodeReviewerSystem(Component):
    """System management for codereviewer plugin."""

    implements(IEnvironmentSetupParticipant, IPermissionRequestor)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self, db=None):
        current_db_version = self._get_version()
        if current_db_version < DB_VERSION:
            return True
        if current_db_version > DB_VERSION:
            raise TracError(_("Database newer than CodeReviewer version"))
        return False

    def upgrade_environment(self, db=None):
        current_db_version = self._get_version()
        with self.env.db_transaction as db:
            cursor = db.cursor()
            for i in range(current_db_version + 1, DB_VERSION + 1):
                name = 'db%i' % i
                try:
                    upgrades = __import__('upgrades', globals(),
                                          locals(), [name])
                    script = getattr(upgrades, name)
                except AttributeError:
                    raise TracError(_("No CodeReviewer upgrade module %(num)i "
                                      "(%(version)s.py)", num=i, version=name))
                script.do_upgrade(self.env, cursor)
                self._set_version(i)

    def _get_version(self):
        value = self.env.db_query("""
            SELECT value FROM system WHERE name=%s
            """, (DB_NAME,))
        return int(value[0][0]) if value else 0

    def _set_version(self, ver):
        if self._get_version() == 0:
            self.env.db_transaction("""
                INSERT INTO system (value,name) VALUES (%s,%s)
                """, (ver, DB_NAME))
        else:
            self.env.db_transaction("""
                UPDATE system SET value=%s WHERE name=%s
                """, (ver, DB_NAME))

        self.log.info("Upgraded CodeReviewer version from %d to %d",
                      ver-1, ver)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['CODEREVIEWER_MODIFY']
