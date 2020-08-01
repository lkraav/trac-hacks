# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from trac.core import Component, ExtensionPoint
from trac.perm import IPermissionGroupProvider, PermissionSystem
from trac.util import to_list
from trac.web.chrome import add_warning


class SmpModel(Component):
    # needed in self.is_not_in_restricted_users()
    group_providers = ExtensionPoint(IPermissionGroupProvider)

    # Common Methods

    def get_project_info(self, name):
        for row in self.env.db_query("""
                SELECT id_project,name,summary,description,closed,restrict_to
                FROM smp_project WHERE name =%s
                """, (name,)):
            return row

    def get_all_projects(self):
        projects = self.env.db_query("""
                SELECT id_project,name,summary,description,closed,restrict_to
                FROM smp_project
                """)

        project_names = [r[1] for r in sorted(projects, key=lambda k: k[1])]
        self.config.set('ticket-custom', 'project.options',
                        '|'.join(project_names))

        return projects

    def get_all_projects_filtered_by_conditions(self, req):
        all_projects = self.get_all_projects()
        for project in list(all_projects):  # now filter out
            project_name = project[1]
            project_info = self.get_project_info(project_name)
            self.filter_project_by_conditions(all_projects, project,
                                              project_info, req)
        return all_projects

    def filter_project_by_conditions(self, all_projects, project, project_info,
                                     req):
        if project_info:
            if project_info[4] > 0:
                # column 4 of table smp_project tells if project is closed
                all_projects.remove(project)
            elif self.is_not_in_restricted_users(req.authname, project_info):
                all_projects.remove(project)

    def check_project_permission(self, req, project_name):
        project_info = self.get_project_info(project_name)
        if project_info:
            if self.is_not_in_restricted_users(req.authname, project_info):
                add_warning(req, "no permission for project %s" % project_name)
                req.perm.require('PROJECT_ACCESS')

    def is_not_in_restricted_users(self, username, project_info):
        # column 5 of table smp_project returns the allowed users
        restricted_users = project_info[5]
        if restricted_users:
            allowed = True
            should_invert = False

            restricted_list = to_list(restricted_users)
            # If list starts with "!," (needs comma!), its meaning is inverted.
            if restricted_list[0] == '!':
                should_invert = True

            # detect groups of the current user including the user name
            g = set([username])
            for provider in self.group_providers:
                for group in provider.get_permission_groups(username):
                    g.add(group)
            perms = PermissionSystem(self.env).get_all_permissions()
            repeat = True
            while repeat:
                repeat = False
                for subject, action in perms:
                    if subject in g and not action.isupper() and \
                            action not in g:
                        g.add(action)
                        repeat = True

            # some of the user's groups must be in the restrictions
            g = g.intersection(set(restricted_list))
            if not (g or len(g)):  # current browser user not allowed?
                allowed = False
            if should_invert:
                allowed = not allowed
            return not allowed
        return False

    # AdminPanel Methods

    def insert_project(self, name, summary, description, closed, restrict):
        self.env.db_transaction("""
                INSERT INTO smp_project
                  (name, summary, description, closed, restrict_to)
                VALUES (%s,%s,%s,%s,%s)
                """, (name, summary, description, closed, restrict))

        # Keep internal list of values for ticket-custom field 'project'
        # updated. This list is used for the dropdown on the query page.
        self.get_all_projects()

    # VersionProject Methods

    def get_versions_of_project(self, project):
        return [version for version, in self.env.db_query("""
                SELECT m.version AS version
                FROM smp_project AS p, smp_version_project AS m
                WHERE p.name = %s AND p.id_project = m.id_project
                ORDER BY m.version
                """, (project,))]

    def get_project_version(self, version):
        for name, in self.env.db_query("""
                SELECT name
                FROM smp_project AS p, smp_version_project AS m
                WHERE m.version=%s and m.id_project = p.id_project
                """, (version,)):
            return name

    def get_id_project_version(self, version):
        for id_, in self.env.db_query("""
                SELECT id_project FROM smp_version_project WHERE version=%s
                """, (version,)):
            return id_

    def rename_version_project(self, old_version, new_version):
        self.env.db_transaction("""
            UPDATE smp_version_project
            SET version=%s WHERE version=%s
            """, (new_version, old_version))
