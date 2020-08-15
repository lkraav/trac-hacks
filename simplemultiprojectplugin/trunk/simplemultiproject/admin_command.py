# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2020 Cinc
#
# License: BSD
#
from simplemultiproject.model import Project
from simplemultiproject.smp_model import SmpComponent, SmpMilestone, SmpProject, SmpVersion
from trac.admin import IAdminCommandProvider
from trac.core import Component, implements
from trac.util.text import printout
from trac.util.translation import _


class SmpAdminCommands(Component):
    """Admin commands for the SimpleMultipleProject plugin

    ==  ==
    The following commands are available:

     project add <project> [summary]::
      Add project with name <project> and an optional summary.

     project assign <component|milestone|version> <project> <item>::
      Assign a component|milestone|version named <item> to a project.

     project close <project>::
      Close project.

     project describe <project> <description>::
      Change description of project.

     project list [detailed]::
      Show all defined projects. With parameter "detailed" some additional
      project information is printed.

     project open <project>::
      Open project.

     project remove <project>::
      Remove project.

     project rename <project> <newname>::
      Rename project.

     project restrict <project> <restrictions>::
      Change restrictions of project.

     project summary:: <project> <summary>
      Change summary of project.

     project unassign <component|milestone|version> <item>::
      Remove component|milestone|version named <item> from all projects.
    """

    implements(IAdminCommandProvider)

    def __init__(self):
        self.smp_milestone = SmpMilestone(self.env)
        self.smp_component = SmpComponent(self.env)
        self.smp_version = SmpVersion(self.env)
        self.smp_project = SmpProject(self.env)

    def get_admin_commands(self):
        yield ('project add', '<project> [summary]',
               'Add project with name <project> and an optional summary.',
               None, self._add_project)
        yield ('project assign', '<component|milestone|version> <project> <item>',
               'Assign a component|milestone|version named <item> to a project.',
               None, self._assign_project)
        yield ('project close', '<project>',
               'Close project.',
               None, self._close_project)
        yield ('project describe', '<project> <description>',
               'Change description of project.',
               None, self._change_description)
        yield ('project list', '[detailed]',
               'Show all defined projects. With parameter "detailed" some additional project information is printed.',
               None, self._list_projects)
        yield ('project open', '<project>',
               'Open project.',
               None, self._open_project)
        yield ('project remove', '<project>',
               'Remove project.',
               None, self._remove_project)
        yield ('project rename', '<project> <newname>',
               'Rename project.',
               None, self._rename_project)
        yield ('project restrict', '<project> <Yes|No>',
               'Change restrictions of project.',
               None, self._change_restrictions)
        yield ('project summary', '<project> <summary>',
               'Change summary of project.',
               None, self._change_summary)
        yield ('project unassign', '<component|milestone|version> <item>',
               'Remove component|milestone|version named <item> from all projects.',
               None, self._unassign_project)

    def _print_no_project(self):
        printout(_("Project does not exist."))

    def _not_implemented(self, arg):
        printout("Command not implemented.")

    def _add_project(self, name, summary=""):
        projects = [project.name for project in Project.select(self.env)]
        if name not in projects:
            self.smp_project.add(name, summary=summary, description="", closed=None, restrict_to="")
        else:
            printout(_("Project already exists."))

    def _rename_project(self, name, newname):
        project = self.smp_project.get_project_from_name(name)
        if not project:
            self._print_no_project()
        else:
            self.smp_project.update(project.id, newname, project.summary, project.description,
                                    project.closed, project.restricted)

    def _list_projects(self, detailed_list=""):
        for id_project, name, summary, description, closed, restrict_to \
                in self.smp_project.get_all_projects():
            if detailed_list:
                printout("\n%s:" % name)
                printout("  Summary:\t%s" % summary)
                printout("  Description:\t%s" % description)
                printout("  Restrict to:\t%s" % restrict_to)
                printout("  Closed:\t%s" % closed)
            else:
                printout("%s" % name)

    def _remove_project(self, name):
        project = self.smp_project.get_project_from_name(name)
        if not project:
            self._print_no_project()
        else:
            self.smp_project.delete(project.id)

    def _change_summary(self, name, summary):
        project = self.smp_project.get_project_from_name(name)
        if not project:
            self._print_no_project()
        else:
            self.smp_project.update(project.id, project.name, summary, project.description,
                                    project.closed, project.restricted)

    def _change_description(self, name, description):
        project = self.smp_project.get_project_from_name(name)
        if not project:
            self._print_no_project()
        else:
            self.smp_project.update(project.id, project.name, project.summary, description,
                                    project.closed, project.restricted)

    def _change_restrictions(self, name, restrictions):
        if restrictions.upper() not in  ('YES', 'NO'):
            printout(_("Restriction must be Yes or No."))
            return

        project = self.smp_project.get_project_from_name(name)
        if not project:
            self._print_no_project()
        else:
            restricted = 'YES' if restrictions.upper() == 'YES' else ''
            self.smp_project.update(project.id, project.name, project.summary, project.description,
                                    project.closed, restricted)

    def _close_project(self, name):
        project = self.smp_project.get_project_from_name(name)
        if not project:
            self._print_no_project()
        else:
            if not project.closed:
                from trac.util.datefmt import to_utimestamp, localtz
                from datetime import datetime
                time = to_utimestamp(datetime.now(localtz))
                self.smp_project.update(project.id, project.name, project.summary, project.description,
                                        time, project.restricted)

    def _open_project(self, name):
        project = self.smp_project.get_project_from_name(name)
        if not project:
            self._print_no_project()
        else:
            self.smp_project.update(project.id, project.name, project.summary, project.description,
                                    None, project.restricted)

    def _assign_project(self, what, prj_name, item):
        project = self.smp_project.get_project_from_name(prj_name)
        if not project:
            self._print_no_project()
        else:
            if what == 'component':
                self.smp_component.add(item, project.id)
            elif what == 'milestone':
                self.smp_milestone.add(item, project.id)
            elif what == 'version':
                self.smp_version.add(item, project.id)

    def _unassign_project(self, what, item):
        # TODO: unassign single projects here
        if what == 'component':
            self.smp_component.delete(item)
        elif what == 'milestone':
            self.smp_milestone.delete(item)
        elif what == 'version':
            self.smp_version.delete(item)
        else:
            printout("Parameter 1 must be one of component, milestone or version, was: %s" % what)
