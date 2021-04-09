# -*- coding: utf-8 -*-
# Created by Noah Kantrowitz on 2007-04-02.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.config import ListOption
from trac.core import Component, implements
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor, PermissionSystem

import hidevals.db_default as db_default


class HideValsSystem(Component):
    """Database provider for the TracHideVals plugin."""

    dont_filter = ListOption('hidevals', 'dont_filter',
                             doc='Ticket fields to ignore when filtering.')

    implements(IEnvironmentSetupParticipant, IPermissionRequestor)

    # Public methods

    def visible_fields(self, req):
        fields = {}
        ps = PermissionSystem(self.env)
        with self.env.db_query as db:
            groups = set(ps.get_permission_groups(req.authname))
            groups.add(req.authname)
            for group in groups:
                for f, v in db("""
                        SELECT field, value FROM hidevals WHERE sid = %s
                        """, (group,)):
                    fields.setdefault(f, []).append(v)

        return fields

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.upgrade_environment()

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(db_default.version, db_default.name)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        dbm.upgrade_tables(db_default.tables)
        dbm.set_database_version(db_default.version, db_default.name)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield 'TICKET_HIDEVALS'
