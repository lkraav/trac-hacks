# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from trac import __version__ as VERSION
from trac.core import *
from trac.util.text import to_unicode
from trac.web.chrome import add_warning, add_notice
from trac.perm import PermissionSystem, IPermissionGroupProvider
from trac.db import with_transaction
from environmentSetup import db_version_key, db_version


class SmpModel(Component):
    # needed in self.is_not_in_restricted_users()
    group_providers = ExtensionPoint(IPermissionGroupProvider)

    def __init__(self):
        # Fix for #12393: check for upgraded database before calling self.get_all_projects()
        db = self.env.get_read_db()
        cursor = db.cursor()
        sql = "SELECT value FROM system WHERE name = %s"
        try:
            cursor.execute(sql, [db_version_key])
            # Make sure we have initial data for the ticket-custom field 'project'.
            if int(cursor.fetchone()[0]) == db_version:
                self.get_all_projects()
        except:
            # We catch all and everything here because different database backends
            # may throw different errors (or none at all which means we would get a
            # TypeError for fetchone()[0], e.g. SQlite)

            # We are just installed and the environment isn't upgraded yet
            pass

    # DB Methods
    def __start_transaction(self, db):
        if VERSION < '0.12':
            # deprecated in newer versions
            db.commit()
            db.close()

    # Commons Methods
    def get_project_info(self, name):
        query = """SELECT
                        id_project,name,summary,description,closed,restrict_to
                   FROM
                        smp_project
                   WHERE
                        name = %s"""

        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute(query, [unicode(name)])
        return  cursor.fetchone()

    def get_all_projects(self):
        query = """SELECT
                        id_project,name,summary,description,closed,restrict_to
                   FROM
                        smp_project"""

        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute(query)

        l = list(cursor.fetchall())
        all_projects = [project[1] for project in sorted(l, key=lambda k: k[1])]
        # Set the list of current projects. This way the dropdown on the query page will be properly populated.
        # Note that we don't save the list at all.
        self.env.config.set("ticket-custom", "project.options", "|".join(all_projects))
        return l

    def get_all_projects_filtered_by_conditions(self, req):
        all_projects = self.get_all_projects()

        # now filter out
        if all_projects:
            for project in list(all_projects):
                project_name = project[1]
                project_info = self.get_project_info(project_name)
                self.filter_project_by_conditions(all_projects, project, project_info, req)
        return all_projects

    def filter_project_by_conditions(self, all_projects, project, project_info, req):
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

            restricted_list = [users.strip() for users in restricted_users.split(',')]
            if restricted_list[0] == '!':  # if the list starts with "!," (needs comma!), its meaning is inverted
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
                    if subject in g and not action.isupper() and action not in g:
                        g.add(action)
                        repeat = True

            g = g.intersection(set(restricted_list))  # some of the user's groups must be in the restrictions
            if not (g or len(g)):  # current browser user not allowed?
                allowed = False
            if should_invert:
                allowed = not allowed
            return not allowed
        return False

    def get_project_name(self, project_id):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project
                   WHERE
                        id_project=%s"""

        cursor.execute(query, [str(project_id)])
        result = cursor.fetchone()

        if result:
            name = result[0]
        else:
            name = None
        return name

    def update_custom_ticket_field(self, old_project_name, new_project_name):
        query    = """UPDATE
                        ticket_custom
                      SET
                        value = %s
                      WHERE
                        name = 'project' AND value = %s"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [new_project_name, old_project_name])

    # AdminPanel Methods
    def insert_project(self, name, summary, description, closed, restrict):
        query    = """INSERT INTO
                        smp_project (name, summary, description, closed, restrict_to)
                      VALUES (%s, %s, %s, %s, %s);"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [name, summary, description, closed, restrict])

        # Keep internal list of values for ticket-custom field 'project' updated. This list is used for the dropdown
        # on the query page
        self.get_all_projects()

    def delete_project(self, ids_projects):
        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            for id in ids_projects:
                query = """DELETE FROM smp_project WHERE id_project=%s"""
                cursor.execute(query, [id])
                query = """DELETE FROM smp_milestone_project WHERE id_project=%s;"""
                cursor.execute(query, [id])
                query = """DELETE FROM smp_version_project WHERE id_project=%s;"""
                cursor.execute(query, [id])
                query = """DELETE FROM smp_component_project WHERE id_project=%s;"""
                cursor.execute(query, [id])

        # Keep internal list of values for ticket-custom field 'project' updated. This list is used for the dropdown
        # on the query page
        self.get_all_projects()

    def update_project(self, id, name, summary, description, closed, restrict):
        query = """UPDATE
                        smp_project
                      SET
                        name = %s, summary = %s, description = %s, closed = %s, restrict_to = %s
                      WHERE
                        id_project = %s"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [name, summary, description, closed, restrict, id])

    # Ticket Methods
    def get_ticket_project(self, id):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT value
                   FROM
                        ticket_custom
                   WHERE
                        name = 'project' AND ticket = %s"""
        cursor.execute(query, [id])
        self.__start_transaction(db)

        return cursor.fetchone()

    # MilestoneProject Methods

    def get_milestones_of_project(self,project):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT
                        m.milestone AS milestone
                   FROM
                        smp_project AS p,
                        smp_milestone_project AS m
                   WHERE
                        p.name = %s AND
                        p.id_project = m.id_project"""

        cursor.execute(query, [project])
        return cursor.fetchall()

    # VersionProject Methods
    def insert_version_project(self, version, id_project):
        query = """INSERT INTO
                        smp_version_project(version, id_project)
                    VALUES (%s, %s)"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [version, str(id_project)])

    def get_versions_of_project(self, project):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT
                        m.version AS version
                   FROM
                        smp_project AS p,
                        smp_version_project AS m
                   WHERE
                        p.name = %s AND
                        p.id_project = m.id_project"""

        cursor.execute(query, [project])
        return sorted(cursor.fetchall())

    def get_project_version(self, version):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project AS p,
                        smp_version_project AS m
                   WHERE
                        m.version=%s and
                        m.id_project = p.id_project"""

        cursor.execute(query, [version])
        return cursor.fetchone()

    def get_id_project_version(self, version):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_version_project
                   WHERE
                        version=%s;"""

        cursor.execute(query, [version])
        return cursor.fetchone()

    def delete_version_project(self, version):
        query = """DELETE FROM
                        smp_version_project
                   WHERE
                        version=%s;"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [version])

    def update_version_project(self, version, project):
        query = """UPDATE
                        smp_version_project
                   SET
                        id_project=%s WHERE version=%s;"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [str(project), version])

    def rename_version_project(self, old_version, new_version):
        query = """UPDATE
                        smp_version_project
                   SET
                        version=%s WHERE version=%s;"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [new_version, old_version])

    # ComponentProject Methods
    def insert_component_projects(self, component, id_projects):
        if not id_projects:
            return

        if type(id_projects) is not list:
            id_projects = [id_projects]

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            for id_project in id_projects:
                query = """INSERT INTO smp_component_project(component, id_project) VALUES (%s, %s)"""
                cursor.execute(query, [component, id_project])

    def get_projects_component(self, component):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT
                        name
                   FROM
                        smp_project AS p,
                        smp_component_project AS m
                   WHERE
                        m.component=%s and
                        m.id_project = p.id_project"""

        cursor.execute(query, [component])
        return cursor.fetchall()

    def get_id_projects_component(self, component):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT
                        id_project
                   FROM
                        smp_component_project
                   WHERE
                        component=%s;"""

        cursor.execute(query, [component])
        return cursor.fetchall()

    def delete_component_projects(self, component):
        query = """DELETE FROM
                        smp_component_project
                   WHERE
                        component=%s;"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [component])

    def rename_component_project(self, old_component, new_component):
        query = """UPDATE
                        smp_component_project
                   SET
                        component=%s WHERE component=%s;"""

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(query, [new_component, old_component])

    def is_milestone_completed(self, milestone_name):
        db = self.env.get_read_db()
        cursor = db.cursor()
        query = """SELECT completed FROM milestone WHERE name=%s;"""
        cursor.execute(query, [milestone_name])
        msCompletedDate = cursor.fetchone()

        if msCompletedDate and msCompletedDate[0] > 0:
            return True
        return False