# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from operator import itemgetter

from trac.admin.api import IAdminPanelProvider
from trac.core import *
from trac.config import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import Chrome, ITemplateProvider, add_notice
from trac.util.translation import _
from trac.util.datefmt import from_utimestamp, get_datetime_format_hint, \
    parse_date, to_utimestamp, user_time

from simplemultiproject.model import *


class SmpAdminPanel(Component):
    """Admin panel for editing project settings."""

    implements(IPermissionRequestor, IAdminPanelProvider, ITemplateProvider)

    # IPermissionRequestor method

    def get_permission_actions(self):
        """ Permissions supported by the plugin. """
        action = ['PROJECT_SETTINGS_VIEW', 'PROJECT_ADMIN']
        return [action[0],
                (action[1], [action[0]])]

    def __init__(self):
        self.__SmpModel = SmpModel(self.env)

    def add_project(self, name, summary, description, closed, restrict):
        try:
            self.log.info("Simple Multi Project: Adding project %s", name)
            self.__SmpModel.insert_project(name, summary, description, closed, restrict)
            # Make sure the internal list of projects is up to date
            self.__SmpModel.get_all_projects()
            self.config.save()  # Fixes #12524
            return True
        except Exception, e:
            self.log.error("Add Project Error: %s", e)
            return False

    def update_project(self, id, name, summary, description, closed, restrict):
        try:
            # we have to rename the project in tickets custom field
            old_project_name = self.__SmpModel.get_project_name(id)

            self.log.info("Simple Multi Project: Modify project %s", name)
            self.__SmpModel.update_project(id, name, summary, description, closed, restrict)

            if old_project_name and old_project_name != name:
                self.__SmpModel.update_custom_ticket_field(old_project_name, name)
            # Make sure the internal list of projects is up to date
            self.__SmpModel.get_all_projects()
            self.config.save()  # Fixes #12524
            return True
        except Exception, e:
            self.log.error("Modify Project Error: %s", e)
            return False

    def render_admin_panel(self, req, category, page, path_info):
        """Return the template and data used to render our administration page.
        """
        data = {}
        req.perm.require('PROJECT_SETTINGS_VIEW')
        projects_rows = self.__SmpModel.get_all_projects()
        projects = []
        for row in sorted(projects_rows, key=itemgetter(1)):
            time_str = None
            timestamp = row[4]
            if (timestamp > 0):
                time_str = from_utimestamp(timestamp)
            projects.append({
                'id': row[0],
                'name': row[1],
                'summary': row[2],
                'description': row[3],
                'closed': time_str,
                'restrict': row[5]
            })

        if path_info:
            if req.method == 'POST':
                if req.args.get('modify'):
                    req.perm.require('PROJECT_ADMIN')

                    time = req.args.get('time', '')
                    if time:
                        time = user_time(req, parse_date, time,
                                         hint='datetime')
                    else:
                        time = None
                    time = to_utimestamp(time)

                    if not self.update_project(req.args.get('id'),
                                               req.args.get('name'),
                                               req.args.get('summary'),
                                               req.args.get('description'),
                                               time, req.args.get('restrict')):
                        self.log.error("SimpleMultiProject Error: Failed to "
                                       "add project '%s'",
                                       req.args.get('name'))
                    else:
                        add_notice(req, "'The project '%s' has been modified."
                                        % req.args.get('name'))
                        req.redirect(req.href.admin(category, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(category, page))
                else:
                    pass
            else:
                for project in projects:
                    if project['id'] == int(path_info):
                        data = {
                            'view': 'detail',
                            'project': project,
                            'datetime_hint': get_datetime_format_hint()
                        }  # vars given to adminpanel.html
        else:
            if req.method == 'POST':
                if req.args.get('add'):
                    req.perm.require('PROJECT_ADMIN')
                    if req.args.get('name') != '':
                        time = req.args.get('time', '')
                        if time:
                            time = user_time(req, parse_date, time,
                                             hint='datetime')
                        else:
                            time = None
                        time = to_utimestamp(time)

                        if not self.add_project(req.args.get('name'),
                                                req.args.get('summary'),
                                                req.args.get('description'),
                                                time,
                                                req.args.get('restrict')):
                            self.log.error("SimpleMultiProject Error: Failed "
                                           "to add project '%s'",
                                           req.args.get('name'))
                        else:
                            add_notice(req, "'The project '%s' has been added."
                                            % req.args.get('name'))
                            req.redirect(req.href.admin(category, page))

                    else:
                        raise TracError('No name input')

                elif req.args.get('remove'):
                    req.perm.require('PROJECT_ADMIN')
                    sel = req.args.getlist('sel')
                    if not sel:
                        raise TracError('No project selected')

                    self.__SmpModel.delete_project(sel)

                    req.redirect(req.href.admin(category, page))

                else:
                    pass
            else:
                data = {
                    'view': 'init',
                    'projects': projects,
                    'datetime_hint': get_datetime_format_hint()
                }

        if hasattr(Chrome(self.env), 'jenv'):
            return 'simplemultiproject_adminpanel.html', data, None
        else:
            return 'simplemultiproject_adminpanel.html', data

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('simplemultiproject', resource_filename(__name__, 'htdocs'))]

    def get_admin_panels(self, req):
        if 'PROJECT_SETTINGS_VIEW' in req.perm('projects'):
            yield ('projects', _('Manage Projects'),
                   'simplemultiproject', _('Projects'))

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
