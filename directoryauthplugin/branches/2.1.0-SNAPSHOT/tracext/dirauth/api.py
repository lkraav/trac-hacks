# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 John Hampton <pacopablo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>

from trac.perm import DefaultPermissionStore

__all__ = ['UserExtensiblePermissionStore']

class UserExtensiblePermissionStore(DefaultPermissionStore):
    """ Default Permission Store extended to list all ldap groups """

    def get_all_permissions(self):
        """Return all permissions for all users.

        The permissions are returned as a list of (subject, action)
        formatted tuples."""
        self.log.debug("calling super.get_all_permissions")
        permissions = super(UserExtensiblePermissionStore, self).get_all_permissions()
        self.log.debug("super.get_all_permissions: %s" % permissions)

        daProvider = None
        for provider in self.group_providers:
            if provider.__class__.__name__ == "DirAuthStore":
                daProvider = provider

        if daProvider == None:
            return permissions

        filteredPermissions = [];
        for p in permissions:
            if p[1][0:1] != "@":
                filteredPermissions.append(p)

        all_groups = daProvider.get_all_groups()
        for g in all_groups:
            users = daProvider.get_group_users(g[1]['cn'][0])
            if len(users) == 0:
                users.append("(nobody)")
            for u in users:
                filteredPermissions.append([u, "@%s" % g[1]['cn'][0]])

        self.log.debug("permissions: %s" % filteredPermissions)
        return filteredPermissions
