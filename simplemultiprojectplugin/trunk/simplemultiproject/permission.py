# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from trac.core import Component as TracComponent, implements
from trac.perm import IPermissionRequestor, IPermissionPolicy, PermissionSystem
from trac.ticket.model import Component, Version
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data
from simplemultiproject.smp_model import PERM_TEMPLATE, SmpComponent, SmpMilestone, SmpProject, SmpVersion


def get_user_projects(req, smp_project):
    """Get all projects user has access to."""
    usr_projects = []
    for project in smp_project.get_all_projects():  # This is already sorted by name
        if project.restricted:
            if (PERM_TEMPLATE % project.id) in req.perm:
                usr_projects.append(project)
        else:
            usr_projects.append(project)
    return usr_projects

def get_user_components(req, smp_component, comp_iterator):
    """Get all components the user has access to.
    :param req: Trac Request object
    :param comp_iterator: iterator of all components as returned by Component.select()
    :returns list of component names
    """
    # Get components with projects
    components = defaultdict(list)  # key: component name, val: list of project ids
    for comp in smp_component.get_all_components_and_project_id():
        components[comp[0]].append(comp[1])  # comp[0]: name, comp[1]: project id

    comps = []
    for comp in comp_iterator:
        if comp.name in components:
            project_ids = components[comp.name]
            for prj_id in project_ids:
                if (PERM_TEMPLATE % prj_id) in req.perm:
                    comps.append(comp.name)
                    break
            del components[comp.name]
        else:
            # Component names without projects
            comps.append(comp.name)

    return sorted(comps)


def get_user_versions(req, smp_version, version_iterator):
    """Get all versions user has access to.
    :param req: Trac Request object
    :param version_iterator: iterator for all versions as returned by Version.select()
    :returns list of version names
    """
    # Get components with projects
    versions = defaultdict(list)  # key: component name, val: list of project ids
    for ver in smp_version.get_all_versions_and_project_id():
        versions[ver[0]].append(ver[1])  # ver[0]: name, ver[1]: project id

    vers = []
    for version in version_iterator:
        if version.name in versions:
            project_ids = versions[version.name]
            for prj_id in project_ids:
                if (PERM_TEMPLATE % prj_id) in req.perm:
                    vers.append(version.name)
                    break
            del versions[version.name]
        else:
            # Component names without projects
            vers.append(version.name)

    return sorted(vers)


class SmpPermissionPolicy(TracComponent):
    """Implements the permission system for SimpleMultipleProject."""
    implements(IRequestFilter, IPermissionPolicy, IPermissionRequestor)

    def __init__(self):
        self.smp_project = SmpProject(self.env)
        self.smp_component = SmpComponent(self.env)
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_version = SmpVersion(self.env)

    # IRequestFilter Methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        # Filter data by permission for the query page
        # Note that milestones are filtered by the permission policy

        if data and template == "query.html":
            # TODO: create project mappings here and change milestone, components and version lists
            # when project is changed

            # Limit projects to those we have access to
            try:
                field = data['fields']['project']
            except KeyError:
                pass
            else:
                projects = get_user_projects(req, self.smp_project)
                field['options'] = [project.name for project in projects]
            # Limit components to those we have access to
            try:
                field = data['fields']['component']
            except KeyError:
                pass
            else:
                comps = get_user_components(req, self.smp_component, Component.select(self.env))
                field['options'] = [comp for comp in comps]
            # Limit versions to those we have access to
            try:
                field = data['fields']['version']
            except KeyError:
                pass
            else:
                vers = get_user_versions(req, self.smp_version, Version.select(self.env))
                field['options'] = [ver for ver in vers]
        elif data and template == "admin_perms.html":
            # Add the project name as a title to all permissions on the Trac permission page.
            # This way the tooltip shows the project name. 'This works at least with installed
            # AccountManagerPlugin
            prj_perms = {"PROJECT_%s_MEMBER" % id_: name for name, id_ in self.smp_project.get_name_and_id()}
            add_script_data(req, {'smp_permissions': prj_perms})
            add_script(req, 'simplemultiproject/js/admin_prefs.js')

        return template, data, content_type

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
        """Check if user has access to this milestone. Returns True if access is possible otherwise False-"""
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

        actions = ["PROJECT_%s_MEMBER" % id_ for name, id_ in self.smp_project.get_name_and_id()] \
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
