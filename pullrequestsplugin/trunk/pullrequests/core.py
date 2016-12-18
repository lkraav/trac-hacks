# -*- coding: utf-8 -*-

import pkg_resources

from trac.db.api import DatabaseManager
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider

from pullrequests.model import SCHEMA


PLUGIN_NAME = 'PullRequestsPlugin'
PLUGIN_VERSION = 1


class PullRequestsModule(Component):
    """Pull Requests."""

    implements(IPermissionRequestor, IEnvironmentSetupParticipant, ITemplateProvider)

    # IPermissionRequestor methods
    
    def get_permission_actions(self):
        actions = ['PULL_REQUEST']
        return actions + [('PULL_REQUEST_ADMIN', actions)]

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
            dbm.upgrade(PLUGIN_VERSION, PLUGIN_NAME, 'pullrequests.upgrades')

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('pullrequests', 'templates')]
