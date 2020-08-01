# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from trac.core import Component as TracComponent, implements
from trac.ticket.model import Component, Version
from trac.web.api import IRequestFilter
from simplemultiproject.smp_model import PERM_TEMPLATE, SmpComponent, SmpProject, SmpVersion


class SmpTicket(TracComponent):
    """Filtering of components for now"""
    implements(IRequestFilter)

    def __init__(self):
        self.smp_project = SmpProject(self.env)
        self.smp_component = SmpComponent(self.env)
        self.smp_version = SmpVersion(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if data and template == "ticket.html":
            # Create a new list of available components for the ticket
            try:
                comp_field = data['fields_map']['component']
            except KeyError:
                pass  # May have been filtered but one of the ticket field filter plugins
            else:
                data['fields'][comp_field]['options'] = self.get_components_for_user(req)

            # Create a new list of available projects for the ticket
            try:
                field = data['fields_map']['project']
            except KeyError:
                pass  # May have been filtered but one of the ticket field filter plugins
            else:
                data['fields'][field]['options'] = self.get_projects_for_user(req)

            # Create a new list of available versions for the ticket
            try:
                field = data['fields_map']['version']
            except KeyError:
                pass  # May have been filtered but one of the ticket field filter plugins
            else:
                data['fields'][field]['options'] = self.get_versions_for_user(req)

        return template, data, content_type

    def get_components_for_user(self, req):
        """Get all components the user has access to.
        :param req: Trac Request object
        :returns list of component names
        """
        # dict with key: milestone, val: list of project ids
        components = defaultdict(list)
        for comp in self.smp_component.get_all_components_and_project_id():
            components[comp[0]].append(comp[1])  # comp[0]: name, comp[1]: project id

        comps = []
        all_comps = Component.select(self.env)
        for comp in all_comps:
            if comp.name in components:
                project_ids = components[comp.name]
                for project in project_ids:
                    if (PERM_TEMPLATE % project) in req.perm:
                        comps.append(comp.name)
                del components[comp.name]
            else:
                comps.append(comp.name)

        return comps

    def get_projects_for_user(self, req):
        """Get all projects user has access to.
        :param req: Trac Request object
        :returns list of project names
        """
        projects = self.smp_project.get_all_projects()
        usr_projects = []
        for project in projects:
            if (PERM_TEMPLATE % project.id) in req.perm:
                usr_projects.append(project.name)
        return usr_projects

    def get_versions_for_user(self, req):
        """Get all versions the user has access to.
        :param req: Trac Request object
        :returns list of version names
        """
        # dict with key: milestone, val: list of project ids
        versions = defaultdict(list)
        for ver in self.smp_version.get_all_versions_and_project_id():
            versions[ver[0]].append(ver[1])  # ver[0]: name, ver[1]: project id

        vers = []
        all_vers = Version.select(self.env)
        for ver in all_vers:
            if ver.name in versions:
                project_ids = versions[ver.name]
                for project in project_ids:
                    if (PERM_TEMPLATE % project) in req.perm:
                        vers.append(ver.name)
                del versions[ver.name]
            else:
                vers.append(ver.name)

        return vers
