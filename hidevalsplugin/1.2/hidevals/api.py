# Created by Noah Kantrowitz on 2007-04-02.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.config import ListOption
from trac.core import Component, ExtensionPoint, implements
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import (
    IPermissionGroupProvider, IPermissionRequestor, PermissionSystem)

import db_default

if not hasattr(PermissionSystem, 'get_permission_groups'):

    PermissionSystem.group_providers = ExtensionPoint(IPermissionGroupProvider)

    def get_permission_groups(self, user):
        groups = set([user])
        for provider in self.group_providers:
            for group in provider.get_permission_groups(user):
                groups.add(group)

        perms = PermissionSystem(self.env).get_all_permissions()
        repeat = True
        while repeat:
            repeat = False
            for subject, action in perms:
                if subject in groups and not action.isupper() and \
                        action not in groups:
                    groups.add(action)
                    repeat = True
        return groups

    PermissionSystem.get_permission_groups = get_permission_groups


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
