# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: BSD
#
from trac import __version__ as trac_version
from trac.db import with_transaction
from simplemultiproject.model import SmpModel

__author__ = 'Cinc'


class SmpBaseModel(object):

    def __init__(self, env):
        self.env = env
        # for V0.11 only
        self._SmpModel = SmpModel(env)

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

    def _all_names_and_id_project(self, resource_name):
        if trac_version < '0.12':
            db = self.env.get_db_cnx()
        else:
            db = self.env.get_read_db()
        cursor = db.cursor()
        sql = """SELECT %s, id_project FROM smp_%s_project;""" % (resource_name, resource_name)
        cursor.execute(sql)
        return cursor.fetchall()


class SmpComponent(SmpBaseModel):
    def __init__(self, env):
        super(SmpComponent, self).__init__(env)

    def delete(self, component_name):
        """Delete a component from the projects database."""
        if trac_version < '0.12':
             self._SmpModel.delete_component_projects(component_name)
        else:
            self._delete_from_db( 'component', component_name)

    def add(self, component_name, id_projects):
        """Add component to each given project.

        :param component_name: name of the component
        :param id_projects: a single project id or a list of project ids
        """
        if trac_version < '0.12':
             self._SmpModel.insert_component_projects(component_name, id_projects)
        else:
            self._insert('component', component_name, id_projects)

    def add_after_delete(self, component_name, id_projects):
        """Delete a component from the database and add it again for the given projects"""
        self.delete(component_name)
        self.add(component_name, id_projects)

    def all_components_and_id_project(self):
        """Get all components with associated project ids

        :return a list of tuples (component_name, project_id)
        """
        return self._all_names_and_id_project('component')


class SmpProject(SmpBaseModel):
    def __init__(self, env):
        super(SmpProject, self).__init__(env)

    def get_name_and_id(self):

        if trac_version < '0.12':
            db = self.env.get_db_cnx()
        else:
            db = self.env.get_read_db()
        cursor = db.cursor()
        sql = """SELECT name, id_project FROM smp_project;"""
        cursor.execute(sql)
        lst = list(cursor.fetchall())
        return sorted(lst, key=lambda k: k[0])


class SmpVersion(SmpBaseModel):

    def __init__(self, env):
        super(SmpVersion, self).__init__(env)

    def add(self, version_name, id_project):
        """Add version to a project.

        :param version_name: name of the component
        :param id_project: a single project id or a list of project ids
        """
        if type(id_project) is list:
            raise ValueError("A version can only be associated with exactly one project.")

        if trac_version < '0.12':
             self._SmpModel.insert_version_project(version_name, id_project)
        else:
            self._insert('version', version_name, [id_project])

    def all_versions_and_id_project(self):
        """Get all versions with associated project id

        :return a list of tuples (version_name, project_id)
        """
        return self._all_names_and_id_project('version')

    def update_project_id_for_version(self, version_name, id_project):
        """TODO: get rid of old model"""
        self._SmpModel.update_version_project(version_name, id_project)
