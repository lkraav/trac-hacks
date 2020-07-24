# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#

from trac.core import Component, implements
from trac.perm import IPermissionRequestor, IPermissionPolicy
from simplemultiproject.smp_model import SmpProject

class SmpPermission(Component):
    """Implements the permission system for SimpleMultipleProject."""
    implements(IPermissionRequestor, IPermissionPolicy)

    # IPermissionRequestor method

    def get_permission_actions(self):
        """ Permissions supported by the plugin. """

        # Permissions for administration
        admin_action = ['PROJECT_SETTINGS_VIEW', 'PROJECT_ADMIN']

        actions = ["PROJECT_%s_MEMBER" % id_ for name, id_ in SmpProject(self.env).get_name_and_id()] \
            + [admin_action[0]]

        # Define actions PROJECT_ADMIN is allowed to perform
        prj_admin = (admin_action[1], [item for item in actions])
        actions.append(prj_admin)

        # return actions
        return [admin_action[0], (admin_action[1], [admin_action[0]])]

    # IPermissionPolicy methods

    def check_permission(self, action, username, resource, perm):

        return None  # We don't care, let another policy check the item