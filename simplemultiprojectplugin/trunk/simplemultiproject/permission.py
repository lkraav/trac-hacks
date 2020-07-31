# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from trac.core import Component, implements
from trac.perm import IPermissionRequestor, IPermissionPolicy, PermissionSystem
from simplemultiproject.smp_model import PERM_TEMPLATE, SmpMilestone, SmpProject


class SmpPermissionPolicy(Component):
    """Implements the permission system for SimpleMultipleProject."""
    implements(IPermissionRequestor, IPermissionPolicy)

    def __init__(self):
        self.smp_project = SmpProject(self.env)
        self.smp_milestone = SmpMilestone(self.env)

    @staticmethod
    def active_projects_by_permission(req, projects):
        filtered = []
        for project in projects:
            if not project.closed:
                if project.restricted:
                    action = PERM_TEMPLATE % project.id
                    if action in req.perm:
                        filtered.append(project)
                else:
                    filtered.append(project)
        return filtered

    def check_milestone_permission(self, milestone, perm):
        """Check if user has access tothis milestone. Returns True if access is possible otherwise False-"""
        # dict with key: milestone, val: list of project ids
        milestones = defaultdict(list)
        for ms in self.smp_milestone.get_all_milestones_and_id_project_id():
            milestones[ms[0]].append(ms[1])

        project_ids = milestones[milestone]
        if not project_ids:
            # This is a milestone without associated project. It was inserted by defaultdict during
            # first access. With normal dict this would have been a KeyError.
            return True
        else:
            for project in project_ids:
                if (PERM_TEMPLATE % project) in perm:
                    return True

        return False

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
                if resource.realm in ('ticket', 'milestone'):
                    break
                resource = resource.parent
            if resource and resource.realm == 'ticket' and resource.id is not None:
                # self.log.info("### Fine grained check: %s %s ressource: %s, realm: %s, id: %s" %
                #               (action, username, resource, resource.realm, resource.id))
                project = self.smp_project.get_project_from_ticket(resource.id)
                if project:
                    if project.restricted and ("PROJECT_%s_MEMBER" % project.id) not in perm:
                        return False  # We deny access no matter what other policies may have decided
            elif resource and resource.realm == 'milestone' and resource.id is not None:
                    # res = self.check_milestone_permission(resource.id, perm)
                    # self.log.info('################# %s %s %s', resource, resource.realm, res)
                    return self.check_milestone_permission(resource.id, perm)

        return None  # We don't care, let another policy check the item
