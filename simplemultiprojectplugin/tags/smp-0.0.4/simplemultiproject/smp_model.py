# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: BSD
#

from trac.db import with_transaction
from simplemultiproject.model import SmpModel
from trac.ticket.model import Version

__author__ = 'Cinc'

__all__ = ['SmpMilestone', 'SmpComponent', 'SmpProject', 'SmpVersion']


class SmpBaseModel(object):
    """Base class for models providing the database access"""
    def __init__(self, env):
        self.env = env
        self.SmpModel = SmpModel(env)
        self.resource_name = "base"

    def _delete_from_db(self, resource_name, name):
        sql = """DELETE FROM smp_%s_project WHERE %s=%%s;""" % (resource_name, resource_name)

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            cursor.execute(sql, [name])

    def _insert(self, resource_name, name, id_projects):
        """For each project id insert a row into the db

        :param resource_name : 'component', 'milestone', 'version'
        :param id_projects: a single project id or a list of ids

        The table name is constructed from the given resource name.
        """
        if not id_projects:
            return
        sql = "INSERT INTO smp_%s_project (%s, id_project) VALUES (%%s, %%s)" % (resource_name, resource_name)
        if type(id_projects) is not list:
            id_projects = [id_projects]

        @with_transaction(self.env)
        def execute_sql_statement(db):
            cursor = db.cursor()
            for id_proj in id_projects:
                cursor.execute(sql, [name, unicode(id_proj)])

    def _get_all_names_and_project_id_for_resource(self, resource_name):
        db = self.env.get_read_db()
        cursor = db.cursor()
        sql = """SELECT %s, id_project FROM smp_%s_project;""" % (resource_name, resource_name)
        cursor.execute(sql)
        return cursor.fetchall()

    def _update(self, resource_name, name, id_projects):

        sql = """UPDATE smp_%s_project SET id_project=%%s WHERE %s=%%s;""" % (resource_name, resource_name)

        @with_transaction(self.env)
        def do_execute(db):
            cursor = db.cursor()
            cursor.execute(sql, (id_projects, name))

    def get_project_names_for_resource_item(self, resource_name, name):
        """Get a list of project names the item of type resource_name is associated with.

        @param resource_name: may be any of component, version, milestone.
        @param name: name of the item e.g. a component name
        @return: a list of project names
        """
        db = self.env.get_read_db()
        cursor = db.cursor()
        sql = "SELECT name FROM smp_project AS p, smp_%s_project AS res WHERE p.id_project = res.id_project " \
              "AND res.%s = %%s" % (resource_name, resource_name)
        cursor.execute(sql, [name])
        return [proj[0] for proj in cursor]  # Convert list of tuples to list of project names

    def get_project_ids_for_resource_item(self, resource_name, name):
        """Get a list of project ids the item of type resource_name is associated with.

        @param resource_name: may be any of component, version, milestone.
        @param name: name of the item e.g. a component name
        @return: a list of project ids
        """
        db = self.env.get_read_db()
        cursor = db.cursor()
        sql = "SELECT id_project FROM smp_%s_project WHERE "\
              "%s = %%s" % (resource_name, resource_name)
        cursor.execute(sql, [name])
        return [proj[0] for proj in cursor]  # Convert list of tuples to list of project names

    def get_resource_items_for_project_id(self, resource_name, id_project):
        """Get all items associated with the given project id for a resource.

        :param resource_name: one of component, milestone, version
        :param id_project: a project id
        :return: a list of one or more items
        """
        db = self.env.get_read_db()
        cursor = db.cursor()
        sql = """SELECT %s FROM smp_%s_project WHERE id_project = %%s ORDER BY id_project;""" %\
              (resource_name, resource_name)
        cursor.execute(sql, [id_project])
        return [item[0] for item in cursor]  # Convert tuples to list items


class SmpComponent(SmpBaseModel):
    """Model for SMP components"""
    def __init__(self, env):
        super(SmpComponent, self).__init__(env)
        self.resource_name = "component"

    def delete(self, component_name):
        """Delete a component from the projects database."""
        self._delete_from_db('component', component_name)

    def add(self, component_name, id_projects):
        """Add component to each given project.

        :param component_name: name of the component
        :param id_projects: a single project id or a list of project ids
        """
        self._insert('component', component_name, id_projects)

    def add_after_delete(self, component_name, id_projects):
        """Delete a component from the SMP database and add it again for the given projects.

        This method is used when the set of projects a component is associated with has changed.
        """
        self.delete(component_name)
        self.add(component_name, id_projects)

    def get_all_components_and_project_id(self):
        """Get all components with associated project ids

        Note that a component may have several project ids and thus will be several times in the tuple.

        :return a list of tuples (component_name, project_id)
        """
        return self._get_all_names_and_project_id_for_resource('component')

    def get_project_names_for_item(self, component):
        """Get a list of all project names the component is associated with"""
        return self.get_project_names_for_resource_item('component', component)

    def get_components_for_project_id(self, id_project):
        """Get components for the given project id.

        :param id_project: a project id
        :return: ordered list of components associated with the given project id. May be empty.
        """
        return self.get_resource_items_for_project_id('component', id_project)


class SmpMilestone(SmpBaseModel):
    def __init__(self, env):
        super(SmpMilestone, self).__init__(env)
        self.resource_name = "milestone"

    def delete(self, milestone_name):
        """Delete a component from the projects database."""
        self._delete_from_db('milestone', milestone_name)

    def add(self, milestone_name, id_projects):
        """Add component to each given project.

        :param milestone_name: name of the milestone
        :param id_projects: a single project id or a list of project ids
        """
        self._insert('milestone', milestone_name, id_projects)

    def add_after_delete(self, milestone_name, id_projects):
        """Delete a milestone from the SMP database and add it again for the given projects.

        This method is used when the set of projects a milestone is associated with has changed.
        """
        self.delete(milestone_name)
        self.add(milestone_name, id_projects)

    def get_all_milestones_and_id_project_id(self):
        """Get all milestones with associated project ids

        Note that a milestone may have several project ids and thus will be several times in the tuple.
        :return a list of tuples (milestone_name, project_id)
        """
        return self._get_all_names_and_project_id_for_resource('milestone')

    def get_project_names_for_item(self, milestone):
        """Get a list of all project names the milestone is associated with"""
        return self.get_project_names_for_resource_item('milestone', milestone)

    def get_milestones_for_project_id(self, id_project):
        """Get milestones for the given project id.

        :param id_project: a project id
        :return: ordered list of milestones associated with the given project id. May be empty.
        """
        return self.get_resource_items_for_project_id('milestone', id_project)


class SmpProject(SmpBaseModel):
    def __init__(self, env):
        super(SmpProject, self).__init__(env)
        # TODO: a call to get_all_projects is missing to fill the custom ticket field.
        # Make sure to look at #12393 when implementing

    def get_name_and_id(self):
        db = self.env.get_read_db()
        cursor = db.cursor()
        sql = """SELECT name, id_project FROM smp_project;"""
        cursor.execute(sql)
        lst = list(cursor.fetchall())
        return sorted(lst, key=lambda k: k[0])

    def get_all_projects(self):
        db = self.env.get_read_db()
        cursor = db.cursor()
        sql = "SELECT id_project, name, summary, description, closed, restrict_to " \
              "FROM smp_project " \
              "ORDER BY name;"
        cursor.execute(sql)

        lst = list(cursor.fetchall())
        all_projects = [proj[1] for proj in lst]
        # Set the list of current projects. This way the dropdown on the query page will be properly populated.
        self.env.config.set("ticket-custom", "project.options", "|".join(all_projects))
        return lst


def get_all_versions_without_project(env):
    """Return a list of all known versions (as unicode) not linked to a project."""
    trac_vers = Version.select(env)

    versions = set(v.name for v in trac_vers) - set(v for v, id_ in SmpVersion(env).get_all_versions_and_project_id())
    return list(versions)


class SmpVersion(SmpBaseModel):

    def __init__(self, env):
        super(SmpVersion, self).__init__(env)
        self.resource_name = "version"

    def delete(self, version_name):
        """Delete a component from the projects database."""
        self._delete_from_db('version', version_name)

    def add(self, version_name, id_project):
        """Add version to a project.

        :param version_name: name of the component
        :param id_project: a single project id or a list of project ids
        """
        self._insert('version', version_name, id_project)

    def add_after_delete(self, version_name, id_projects):
        """Delete a version from the SMP database and add it again for the given projects.

        This method is used when the set of projects a version is associated with has changed.
        """
        self.delete(version_name)
        self.add(version_name, id_projects)

    def get_all_versions_and_project_id(self):
        """Get all versions with associated project id

        :return a list of tuples (version_name, project_id)
        """
        return self._get_all_names_and_project_id_for_resource('version')

    def update_project_id_for_version(self, version_name, id_project):
        """TODO: get rid of old model"""
        self._update('version', version_name, id_project)

    def get_project_names_for_item(self, version):
        """Get a list of all project names the milestone is associated with"""
        return self.get_project_names_for_resource_item('version', version)

    def get_versions_for_project_id(self, id_project):
        """Get versions for the given project id.

        :param id_project: a project id
        :return: ordered list of versions associated with the given project id. May be empty.
        """
        return self.get_resource_items_for_project_id('version', id_project)
