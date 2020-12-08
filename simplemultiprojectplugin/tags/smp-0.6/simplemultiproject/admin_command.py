# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Cinc
#
# License: BSD
#

from trac.admin import IAdminCommandProvider
from trac.core import Component, implements
from trac.util.text import printout
from trac.util.translation import _

from simplemultiproject.model import SmpModel
from simplemultiproject.smp_model import SmpMilestone


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
        self.__SmpModel = SmpModel(self.env)
        self.smp_milestone = SmpMilestone(self.env)

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
        yield ('project restrict', '<project> <restrictions>',
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
        if not self.__SmpModel.get_project_info(name):
            self.__SmpModel.insert_project(name, summary=summary, description="", closed=0, restrict="")
        else:
            printout(_("Project already exists."))

    def _rename_project(self, name, newname):

        dat = self.__SmpModel.get_project_info(name)

        if not dat:
            self._print_no_project()
        else:
            self.__SmpModel.update_project(dat[0], newname, dat[2], dat[3], dat[4], dat[5])
            if newname != name:
                self.__SmpModel.update_custom_ticket_field(name, newname)

    def _list_projects(self, detailed_list=""):
        for id_project, name, summary, description, closed, restrict_to \
                in self.__SmpModel.get_all_projects():
            if detailed_list:
                printout("\n%s:" % name)
                printout("  Summary:\t%s" % summary)
                printout("  Description:\t%s" % description)
                printout("  Restrict to:\t%s" % restrict_to)
                printout("  Closed:\t%s" % closed)
            else:
                printout("%s" % name)

    def _remove_project(self, name):
        dat = self.__SmpModel.get_project_info(name)

        if not dat:
            self._print_no_project()
        else:
            self.__SmpModel.delete_project([dat[0]])

    def _change_summary(self, name, summary):

        dat = self.__SmpModel.get_project_info(name)

        if not dat:
            self._print_no_project()
        else:
            self.__SmpModel.update_project(dat[0], dat[1], summary, dat[3], dat[4], dat[5])

    def _change_description(self, name, description):

        dat = self.__SmpModel.get_project_info(name)

        if not dat:
            self._print_no_project()
        else:
            self.__SmpModel.update_project(dat[0], dat[1], dat[2], description, dat[4], dat[5])

    def _change_restrictions(self, name, restrictions):

        dat = self.__SmpModel.get_project_info(name)

        if not dat:
            self._print_no_project()
        else:
            self.__SmpModel.update_project(dat[0], dat[1], dat[2], dat[3], dat[4], restrictions)

    def _close_project(self, name):

        dat = self.__SmpModel.get_project_info(name)

        if not dat:
            self._print_no_project()
        else:
            if not dat[4]:
                from trac.util.datefmt import to_utimestamp, localtz
                from datetime import datetime
                time = to_utimestamp(datetime.now(localtz))
                self.__SmpModel.update_project(dat[0], dat[1], dat[2], dat[3], time, dat[5])

    def _open_project(self, name):

        dat = self.__SmpModel.get_project_info(name)

        if not dat:
            self._print_no_project()
        else:
            self.__SmpModel.update_project(dat[0], dat[1], dat[2], dat[3], 0, dat[5])

    def _assign_project(self, what, prj_name, item):

        dat = self.__SmpModel.get_project_info(prj_name)

        if not dat:
            self._print_no_project()
        else:
            if what == 'component':
                self.__SmpModel.insert_component_projects(item, dat[0])
            elif what == 'milestone':
                self.smp_milestone.add(item, dat[0])
            elif what == 'version':
                self.__SmpModel.insert_version_project(item, dat[0])

    def _unassign_project(self, what, item):
        if what == 'component':
            self.__SmpModel.delete_component_projects(item)
        elif what == 'milestone':
            self.smp_milestone.delete(item)
        elif what == 'version':
            self.__SmpModel.delete_version_project(item)
        else:
            printout("Parameter 1 must be one of component, milestone or version, was: %s" % what)
