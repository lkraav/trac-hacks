# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Gefasoft AG
# Copyright (C) 2015 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#


from trac.core import Component, implements
from trac.perm import IPermissionRequestor, PermissionSystem

"""
Created on 06.10.2014

@author: barbara.streppel
"""


# ===========================================================================
# accepted permissions for this plugin
# ===========================================================================

permissionListView = [
    "TRAC_ADMIN", "TM_EXPORT", "TM_VIEW", "TM_IMPORT", "TM_EDIT"]
permissionListEdit = ["TRAC_ADMIN", "TM_EXPORT", "TM_IMPORT", "TM_EDIT"]
permissionListExport = ["TRAC_ADMIN", "TM_EXPORT"]
permissionListImport = ["TRAC_ADMIN", "TM_IMPORT"]


# ===========================================================================
# Method returns true, if the given user from the request object meets
# the required demands
# ===========================================================================


def checkPermissionsView(self, req):
    for permission in permissionListView:
        if permission in PermissionSystem(self.env).get_user_permissions(
            req.authname
        ):
            return True
    return False


def checkPermissionsEdit(self, req):
    for permission in permissionListEdit:
        if permission in PermissionSystem(self.env).get_user_permissions(
            req.authname
        ):
            return True
    return False


def checkPermissionsExport(self, req):
    for permission in permissionListExport:
        if permission in PermissionSystem(self.env).get_user_permissions(
            req.authname
        ):
            return True
    return False


def checkPermissionsImport(self, req):
    for permission in permissionListImport:
        if permission in PermissionSystem(self.env).get_user_permissions(
            req.authname
        ):
            return True
    return False


def whatPermission(self, req):
    perm = []
    if checkPermissionsExport(self, req):
        perm.append("export")
    if checkPermissionsImport(self, req):
        perm.append("import")
    if checkPermissionsEdit(self, req):
        perm.append("edit")
    if checkPermissionsView(self, req):
        perm.append("view")
    return perm


# ===========================================================================
# Class to publish an additional Permission Type
# ===========================================================================


class TransPermission(Component):
    implements(IPermissionRequestor)
    """ publicise permission 'TM_VIEW', 'TM_EDIT', 'TM_EXPORT', 'TM_IMPORT'"""

    # IPermissionRequestor

    def get_permission_actions(self):
        return ["TM_VIEW", "TM_EDIT", "TM_EXPORT", "TM_IMPORT"]
