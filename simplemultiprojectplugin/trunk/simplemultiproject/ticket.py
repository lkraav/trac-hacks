# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from trac.core import Component as TracComponent, implements
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data
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
                comps, comp_map = self.get_components_for_user(req, data['fields'][comp_field]['options'])
                data['fields'][comp_field]['options'] = comps
                add_script_data(req, {'smp_component_map': comp_map,
                                      'smp_component_sel': ''})  # used by javascript to hold initial selected component

            # Create a new list of available projects for the ticket
            try:
                field = data['fields_map']['project']
            except KeyError:
                pass  # May have been filtered but one of the ticket field filter plugins
            else:
                projects, project_map = self.get_projects_for_user(req)
                data['fields'][field]['options'] = projects
                add_script_data(req, {'smp_project_map': project_map})

            # Create a new list of available versions for the ticket
            try:
                field = data['fields_map']['version']
            except KeyError:
                pass  # May have been filtered but one of the ticket field filter plugins
            else:
                versions, version_map = self.get_versions_for_user(req, data['fields'][field]['options'],
                                                                   data['fields'][field]['optional'])
                data['fields'][field]['options'] = versions
                add_script_data(req, {'smp_version_map': version_map,
                                      'smp_version_sel': ''})  # used by javascript to hold initial selected component
            comp_warn = _("Project changed. The previous component is no longer available. Check component selection.")
            ver_warn = _("Project changed. The previous version is no longer available. Check version selection.")
            add_script_data(req, {'smp_component_warning':
                                      '<div id="smp-comp-warn" class="system-message warning" '
                                      'style="display: none">%s</div>' % comp_warn,
                                  'smp_version_warning':
                                      '<div id="smp-version-warn" class="system-message warning" '
                                      'style="display: none">%s</div>' % ver_warn
                                  })
            add_script(req, 'simplemultiproject/js/ticket.js')
        return template, data, content_type

    def create_option(self, name):
        return u'<option value="{name}">{name}</option>'.format(name=name)

    def get_components_for_user(self, req, tkt_comps):
        """Get all components the user has access to.
        :param req: Trac Request object
        :param tkt_comps: list of component names taken from the ticket data
        :returns list of component names
        """
        # Get components with projects
        components = defaultdict(list)  # key: component name, val: list of project ids
        for comp in self.smp_component.get_all_components_and_project_id():
            components[comp[0]].append(comp[1])  # comp[0]: name, comp[1]: project id

        # Map project ids to list of component names
        comps = []
        temp = []  # holds component names without any associated project
        comp_map = defaultdict(list)  # key: project id, value: list of components
        for comp in tkt_comps:
            if comp in components:
                project_ids = components[comp]
                for prj_id in project_ids:
                    if (PERM_TEMPLATE % prj_id) in req.perm:
                        comps.append(comp)
                        comp_map[str(prj_id)].append(comp)
                del components[comp]
            else:
                # Component names without projects
                comps.append(comp)
                temp.append(comp)

        temp.sort()
        for project in self.smp_project.get_all_projects():
            if not str(project.id) in comp_map:
                comp_map[str(project.id)] = temp
            else:
                comp_map[str(project.id)] += temp
                comp_map[str(project.id)].sort()

        # Convert to HTML string so javascript can easily replace the options of the select control
        for key, val in comp_map.items():
            options = u''
            for item in val:
                options += self.create_option(item)
            comp_map[key] = options

        return comps, comp_map

    def get_projects_for_user(self, req):
        """Get all projects user has access to.
        :param req: Trac Request object
        :returns list of project names
        """
        projects = self.smp_project.get_all_projects()
        usr_projects = []
        project_map = {}
        for project in projects:
            if project.restricted:
                if (PERM_TEMPLATE % project.id) in req.perm:
                    usr_projects.append(project.name)
                    project_map[project.name] = str(project.id)
            else:
                usr_projects.append(project.name)
                project_map[project.name] = str(project.id)

        return usr_projects, project_map

    def get_versions_for_user(self, req, tkt_vers, optional):
        """Get all versions the user has access to.
        :param req: Trac Request object
        :param tkt_vers: list of versions taken from the ticket data
        :param optional: if True the user may omitt any selection
        :returns list of version names
        """
        # Get versions with projects
        versions = defaultdict(list)  # key: version, val: list of project ids
        for ver in self.smp_version.get_all_versions_and_project_id():
            versions[ver[0]].append(ver[1])  # ver[0]: name, ver[1]: project id

        self.log.info('### %s ', versions)
        # Map project ids to list of version names
        vers = []
        temp = []  # holds version names without any associated project
        ver_map = defaultdict(list)
        for ver in tkt_vers:
            if ver in versions:
                project_ids = versions[ver]
                for prj_id in project_ids:
                    if (PERM_TEMPLATE % prj_id) in req.perm:
                        vers.append(ver)
                        ver_map[str(prj_id)].append(ver)
                del versions[ver]
            else:
                # Version names without projects
                vers.append(ver)
                temp.append(ver)
        temp.sort()
        for project in self.smp_project.get_all_projects():
            if not str(project.id) in ver_map:
                ver_map[str(project.id)] = temp
            else:
                ver_map[str(project.id)] += temp
                ver_map[str(project.id)].sort()
        # Convert to HTML string so javascript can easily replace the options of the select control
        for key, val in ver_map.items():
            options = u'<option></option>' if optional else u''
            for item in val:
                options += self.create_option(item)
            ver_map[key] = options

        return vers, ver_map
