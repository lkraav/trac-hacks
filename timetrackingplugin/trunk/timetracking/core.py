# -*- coding: utf-8 -*-

import pkg_resources

from trac.db.api import DatabaseManager
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider

from timetracking.model import SCHEMA


PLUGIN_NAME = 'TimeTrackingPlugin'
PLUGIN_VERSION = 5


class TimeTrackingModule(Component):
    """Time estimations and logging."""

    implements(IPermissionRequestor, IEnvironmentSetupParticipant, ITemplateProvider)

    # IPermissionRequestor methods
    
    def get_permission_actions(self):
        actions = ['TIME_TRACKING']
        return actions + [('TIME_TRACKING_ADMIN', actions)]

    # IEnvironmentSetupParticipant

    def environment_created(self):
        dbm = DatabaseManager(self.env)
        dbm.create_tables(SCHEMA)
        dbm.set_database_version(PLUGIN_VERSION, PLUGIN_NAME)

    def environment_needs_upgrade(self):
        dbm = DatabaseManager(self.env)
        return dbm.needs_upgrade(PLUGIN_VERSION, PLUGIN_NAME)

    def upgrade_environment(self):
        dbm = DatabaseManager(self.env)
        if dbm.get_database_version(PLUGIN_NAME) == 0:
            dbm.create_tables(SCHEMA)
            dbm.set_database_version(PLUGIN_VERSION, PLUGIN_NAME)
        else:
            dbm.upgrade(PLUGIN_VERSION, PLUGIN_NAME, 'timetracking.upgrades')

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('timetracking', pkg_resources.resource_filename('timetracking', 'htdocs'))]

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('timetracking', 'templates')]

