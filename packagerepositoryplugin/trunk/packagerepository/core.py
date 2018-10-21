# -*- coding: utf-8 -*-

import pkg_resources

from trac.admin import IAdminPanelProvider
from trac.core import *
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import ITemplateProvider

from packagerepository.model import SCHEMA


PLUGIN_NAME = 'PackageRepositoryPlugin'
PLUGIN_VERSION = 1


class IPackageRepositoryProvider(Interface):
    
    def get_repository_types(self):
        """Get repository types handled by this provider.
        
        :return: a list of repository type strings.
        """

    def save_package(self, repository_type, filename, fileobj):
        """Save a package file.

        :param repository_type: the repository type string.
        :param filename: the filename string.
        :param fileobj: the file object.
        """

    def delete_package(self, repository_type, filename):
        """Delete a package file.

        :param repository_type: the repository type string.
        :param filename: the filename string.
        """


class PackageRepositoryModule(Component):
    """Package Repository"""

    implements(IPermissionRequestor, IEnvironmentSetupParticipant, ITemplateProvider)

    package_repository_providers = ExtensionPoint(IPackageRepositoryProvider)

    def get_all_repository_types(self):
        return [repotype for provider in self.package_repository_providers
                         for repotype in provider.get_repository_types()]

    def get_repository_provider(self, repository_type):
        for provider in self.package_repository_providers:
            for repotype in provider.get_repository_types():
                if repotype == repository_type:
                    return provider
        raise TracError("Unknown package repository type %s" % repository_type)

    def save_package(self, repository_type, filename, fileobj):
        provider = self.get_repository_provider(repository_type)
        provider.save_package(repository_type, filename, fileobj)

    def delete_package(self, repository_type, filename):
        provider = self.get_repository_provider(repository_type)
        provider.delete_package(repository_type, filename)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['PACKAGE_REPOSITORY_VIEW']
        return actions + [('PACKAGE_REPOSITORY_ADMIN', actions)]

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
            dbm.upgrade(PLUGIN_VERSION, PLUGIN_NAME, 'packagerepository.upgrades')

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('packagerepository', 'templates')]
