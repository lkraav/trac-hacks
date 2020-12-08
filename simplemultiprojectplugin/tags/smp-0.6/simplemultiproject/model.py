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

    def get_project_name(self, project_id):
        for name, in self.env.db_query("""
                SELECT name FROM smp_project WHERE id_project=%s
                """, (project_id,)):
            return name

    def update_custom_ticket_field(self, old_project_name, new_project_name):
        self.env.db_transaction("""
                UPDATE ticket_custom SET value=%s
                WHERE name='project' AND value=%s
                """, (new_project_name, old_project_name))

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

    def delete_project(self, ids_projects):
        with self.env.db_transaction as db:
            for id_ in ids_projects:
                db("""
                    DELETE FROM smp_project WHERE id_project=%s
                    """, (id_,))
                db("""
                    DELETE FROM smp_milestone_project WHERE id_project=%s
                    """, (id_,))
                db("""
                    DELETE FROM smp_version_project WHERE id_project=%s
                    """, (id_,))
                db("""
                    DELETE FROM smp_component_project WHERE id_project=%s
                    """, (id_,))

        # Keep internal list of values for ticket-custom field 'project'
        # updated. This list is used for the dropdown on the query page.
        self.get_all_projects()

    def update_project(self, id, name, summary, description, closed, restrict):
        self.env.db_transaction("""
            UPDATE smp_project
            SET name=%s, summary=%s, description=%s, closed=%s, restrict_to=%s
            WHERE id_project=%s
            """, (name, summary, description, closed, restrict, id))

    # Ticket Methods

    def get_ticket_project(self, id):
        for project, in self.env.db_query("""
                SELECT value FROM ticket_custom
                WHERE name='project' AND ticket=%s
                """, (id,)):
            return project

    # MilestoneProject Methods

    def get_milestones_of_project(self, project):
        return [milestone for milestone, in self.env.db_query("""
                SELECT m.milestone AS milestone
                FROM smp_project AS p, smp_milestone_project AS m
                WHERE p.name = %s AND p.id_project = m.id_project
                """, (project,))]

    # VersionProject Methods

    def insert_version_project(self, version, id_project):
        self.env.db_transaction("""
                INSERT INTO smp_version_project(version, id_project)
                VALUES (%s,%s)
                """, (version, id_project))

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

    def delete_version_project(self, version):
        self.env.db_transaction("""
            DELETE FROM smp_version_project WHERE version=%s
            """, (version,))

    def update_version_project(self, version, project):
        self.env.db_transaction("""
            UPDATE smp_version_project
            SET id_project=%s WHERE version=%s
            """, (project, version))

    def rename_version_project(self, old_version, new_version):
        self.env.db_transaction("""
            UPDATE smp_version_project
            SET version=%s WHERE version=%s
            """, (new_version, old_version))

    # ComponentProject Methods

    def insert_component_projects(self, component, id_projects):
        if not id_projects:
            return

        if type(id_projects) is not list:
            id_projects = [id_projects]

        with self.env.db_transaction as db:
            for id_project in id_projects:
                db("""
                    INSERT INTO smp_component_project(component, id_project)
                    VALUES (%s, %s)
                    """, (component, id_project))

    def get_projects_component(self, component):
        return [name for name, in self.env.db_query("""
                SELECT name
                FROM smp_project AS p, smp_component_project AS m
                WHERE m.component=%s and m.id_project = p.id_project
                """, (component,))]

    def get_id_projects_component(self, component):
        return [id_project for id_project, in self.env.db_query("""
                SELECT id_project
                FROM smp_component_project WHERE component=%s
                """, (component,))]

    def delete_component_projects(self, component):
        self.env.db_transaction("""
            DELETE FROM smp_component_project WHERE component=%s
            """, (component,))

    def rename_component_project(self, old_component, new_component):
        self.env.db_transaction("""
            UPDATE smp_component_project
            SET component=%s WHERE component=%s
            """, (new_component, old_component))

    def is_milestone_completed(self, milestone_name):
        completed = None
        for completed, in self.env.db_query("""
                SELECT completed FROM milestone WHERE name=%s
                """, (milestone_name,)):
            break
        return completed and completed > 0
