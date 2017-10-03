# Created by Noah Kantrowitz on 2007-04-02.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.config import ListOption
from trac.core import Component, ExtensionPoint, implements
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import (
    IPermissionGroupProvider, IPermissionRequestor, PermissionSystem)

import db_default


class HideValsSystem(Component):
    """Database provider for the TracHideVals plugin."""

    group_providers = ExtensionPoint(IPermissionGroupProvider)

    dont_filter = ListOption('hidevals', 'dont_filter',
                             doc='Ticket fields to ignore when filtering.')

    implements(IPermissionRequestor, IEnvironmentSetupParticipant)

    # Public methods

    def visible_fields(self, req):
        fields = {}
        with self.env.db_query as db:
            for group in self._get_groups(req.authname):
                for f, v in db("""
                        SELECT field, value FROM hidevals WHERE sid = %s
                        """, (group,)):
                    fields.setdefault(f, []).append(v)

        return fields

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield 'TICKET_HIDEVALS'

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

    # Private methods

    def _get_groups(self, user):
        # Get initial subjects
        groups = set([user])
        for provider in self.group_providers:
            for group in provider.get_permission_groups(user):
                groups.add(group)

        perms = PermissionSystem(self.env).get_all_permissions()
        repeat = True
        while repeat:
            repeat = False
            for subject, action in perms:
                if subject in groups and action.islower() and \
                        action not in groups:
                    groups.add(action)
                    repeat = True

        return groups
