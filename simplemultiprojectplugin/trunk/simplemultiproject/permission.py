# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#

from trac.core import Component, implements
from trac.perm import IPermissionRequestor, IPermissionPolicy, PermissionSystem
from simplemultiproject.smp_model import SmpProject


class SmpPermissionPolicy(Component):
    """Implements the permission system for SimpleMultipleProject."""
    implements(IPermissionRequestor, IPermissionPolicy)

    def __init__(self):
        self.smp_project = SmpProject(self.env)

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

        return actions
        #return [admin_action[0], (admin_action[1], [admin_action[0]])]

    # IPermissionPolicy methods

    def check_permission(self, action, username, resource, perm):

        # Avoid recursion
        # This also affects PROJECT_SETTINGS_VIEW but we don't care. DefaultPolicy will take care of it.
        # We are only working with PROJECT_<id>_MEMBER later on.
        if action.startswith('PROJECT_'):
            return

        # Check whether we're dealing with a ticket resource
        if resource: # fine-grained permission check
            while resource:
                if resource.realm == 'ticket':
                    break
                resource = resource.parent
            if resource and resource.realm == 'ticket' and resource.id is not None:
                #self.log.info("### Fine grained check: %s %s ressource: %s, realm: %s, id: %s" %
                #              (action, username, resource, resource.realm, resource.id))
                project = self.smp_project.get_project_from_ticket(resource.id)
                if project:
                    if project.restricted and ("PROJECT_%s_MEMBER" % project.id) not in perm:
                        return False  # We deny access no matter what other policies may have decided

        return None  # We don't care, let another policy check the item
