# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
from collections import defaultdict
from simplemultiproject.model import Project
from simplemultiproject.permission import SmpPermissionPolicy
from simplemultiproject.smp_model import PERM_TEMPLATE, SmpComponent, SmpMilestone, SmpVersion
from trac.config import BoolOption
from trac.core import Component as TracComponent, implements
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, add_script_data


class SmpTicket(TracComponent):
    """Provide allowed projects and components. Filter milestones,
    components and versions according to project selecton."""
    implements(IRequestFilter)

    allow_no_project = BoolOption(
        'simple-multi-project', 'ticket_without_project', False,
        doc="""Set this option to {{{True}}} if you want to create tickets
                   without associated projects. The default value is {{{False}}}.
                   """)

    def __init__(self):
        self.smp_component = SmpComponent(self.env)
        self.smp_version = SmpVersion(self.env)
        self.smp_milestone = SmpMilestone(self.env)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if data and template == "ticket.html":
            # Create a new list of available components and project mapping for the ticket
            try:
                comp_field = data['fields_map']['component']
            except KeyError:
                pass  # May have been filtered by one of the ticket field filter plugins
            else:
                comps, comp_map = self.get_component_project_mapping_for_user(req,
                                                                              data['fields'][comp_field]['options'])
                data['fields'][comp_field]['options'] = comps
                add_script_data(req, {'smp_component_map': comp_map,
                                      'smp_component_sel': ''})  # used by javascript to hold initial selected component

            # Create a new list of available projects for the ticket
            try:
                field = data['fields_map']['project']
            except KeyError:
                pass  # May have been filtered by one of the ticket field filter plugins
            else:
                projects, project_map = self.get_projects_for_user(req)
                data['fields'][field]['options'] = projects
                # Allow for no project
                # TODO: see smp_model->get_all_projects() why this is broken
                # if self.allow_no_project:
                #     data['fields'][field]['optional'] = True
                # else:
                #     data['fields'][field]['optional'] = False
                add_script_data(req, {'smp_project_map': project_map})

            # Create a new list of available versions and project mapping for the ticket
            try:
                field = data['fields_map']['version']
            except KeyError:
                pass  # May have been filtered by one of the ticket field filter plugins
            else:
                # This filters versions the user has no access to
                versions, version_map = self.get_version_project_mapping_for_user(req, data['fields'][field]['options'],
                                                                                  data['fields'][field]['optional'])
                data['fields'][field]['options'] = versions
                add_script_data(req, {'smp_version_map': version_map,
                                      'smp_version_sel': ''})  # used by javascript to hold initial selected component

            comp_warn = _("Project changed. The previous component is not available for this project. "
                          "Check component selection.")
            ver_warn = _("Project changed. The previous version is not available for this project. "
                         "Check version selection.")
            ms_warn = _("Project changed. The previous milestone is not available for this project. "
                        "Check milestone selection.")

            add_script_data(req, {'smp_component_warning':
                                  '<div id="smp-comp-warn" class="system-message warning" '
                                  'style="display: none">%s</div>' % comp_warn,
                                  'smp_version_warning':
                                  '<div id="smp-version-warn" class="system-message warning" '
                                  'style="display: none">%s</div>' % ver_warn,
                                  'smp_milestone_warning':
                                  '<div id="smp-milestone-warn" class="system-message warning" '
                                  'style="display: none">%s</div>' % ms_warn
                                  })
            # Create a new list of available projects for the ticket
            try:
                field = data['fields_map']['milestone']
            except KeyError:
                pass  # May have been filtered by one of the ticket field filter plugins
            else:
                milestone_map = self.get_milestone_project_mapping_for_user(req, data['fields'][field]['optgroups'],
                                                                            data['fields'][field]['optional'])
                add_script_data(req, {'smp_milestone_map': milestone_map,
                                      'smp_milestone_sel': ''})

            add_script(req, 'simplemultiproject/js/ticket.js')
        return template, data, content_type

    def create_option(self, name):
        return u'<option value="{name}">{name}</option>'.format(name=name)

    def get_milestone_project_mapping_for_user(self, req, tkt_ms_groups, optional):
        # Note that milestones filtering by access rights is already done by a permission policy.
        # Get milestones with projects
        milestones = defaultdict(list)  # key: milestone name, val: list of project ids
        for ms in self.smp_milestone.get_all_milestones_and_id_project_id():
            milestones[ms[0]].append(ms[1])  # ms[0]: name, ms[1]: project id

        # We do a project grouping for every optgroup in the milestone data
        ms_group_map = []
        for group in tkt_ms_groups:
            temp = []  # holds milestone names without any associated project
            ms_map = defaultdict(list)  # key: project id, value: list of milestones
            for ms in group['options']:
                if ms in milestones:
                    project_ids = milestones[ms]
                    for prj_id in project_ids:
                        ms_map[str(prj_id)].append(ms)
                    del milestones[ms]
                else:
                    # milestone names without associated projects for this optgroup
                    temp.append(ms)

            # Add project grouping for projects not found in the milestone association table. Add milestones without
            # restrictions to the projects. Add milestones without restrictions to the projects we already found in
            # the milestone table.
            temp.sort()
            for project in Project.select(self.env):
                if not str(project.id) in ms_map:
                    ms_map[str(project.id)] = temp
                else:
                    ms_map[str(project.id)] += temp
                    ms_map[str(project.id)].sort()
            ms_map['0'] = temp  # used, when no project is selected

            # Convert to single optgroup HTML string
            for project_id, ms_list in ms_map.items():
                if ms_list:
                    options_html = u''
                    for item in ms_list:
                        options_html += self.create_option(item)

                    optgroup_html = u'<optgroup label="{label}">{options}</optgroup>'.format(label=group['label'],
                                                                                             options=u'{options}')
                    ms_map[project_id] = optgroup_html.format(options=options_html)
                else:
                    # No milestones for this group so remove the optgroup altogether
                    ms_map[project_id] = u''
            ms_group_map.append(ms_map)

        # build the whole optgroup string for each project id
        optional = u'<option></option>' if optional else u''
        ms_optgroup_map = {key: optional for key in ms_group_map[0]}
        for group in ms_group_map:
            for project_id, optgroup_html in group.items():
                ms_optgroup_map[project_id] += optgroup_html

        return ms_optgroup_map

    def get_component_project_mapping_for_user(self, req, tkt_comps):
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
        for project in Project.select(self.env):
            if not str(project.id) in comp_map:
                comp_map[str(project.id)] = temp
            else:
                comp_map[str(project.id)] += temp
                comp_map[str(project.id)].sort()
        comp_map['0'] = temp  # used, when no project is selected

        # Convert to HTML string so javascript can easily replace the options of the select control
        for key, val in comp_map.items():
            options = u''
            for item in val:
                options += self.create_option(item)
            comp_map[key] = options

        return comps, comp_map

    def get_projects_for_user(self, req):
        """Get all active projects user has access to.

        :param req: Trac Request object
        :returns list of project names, dict with mapping project.name - project.id

        Closed projects are omitted.
        """
        projects = SmpPermissionPolicy.active_projects_by_permission(req, Project.select(self.env))
        project_names = []
        project_map = {}
        for project in projects:
            project_names.append(project.name)
            project_map[project.name] = str(project.id)

        return project_names, project_map

    def get_version_project_mapping_for_user(self, req, tkt_vers, optional):
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
        for project in Project.select(self.env):
            if not str(project.id) in ver_map:
                ver_map[str(project.id)] = temp
            else:
                ver_map[str(project.id)] += temp
                ver_map[str(project.id)].sort()
        ver_map['0'] = temp  # used, when no project is selected

        # Convert to HTML string so javascript can easily replace the options of the select control
        for project_id, val in ver_map.items():
            options = u'<option></option>' if optional else u''
            for item in val:
                options += self.create_option(item)
            ver_map[project_id] = options

        return vers, ver_map
