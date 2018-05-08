# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#

from trac.ticket.model import Version

__all__ = ['SmpMilestone', 'SmpComponent', 'SmpProject', 'SmpVersion']


class SmpBaseModel(object):
    """Base class for models providing the database access"""

    def __init__(self, env):
        self.env = env
        self.resource_name = "base"

    def delete(self, name):
        """Delete item 'name' from database. Name may be a list or a
        single item.

        @param name: single name or list of names.
        """
        if type(name) is not list:
            name = [name]

        with self.env.db_transaction as db:
            for n in name:
                db("""
                    DELETE FROM smp_%s_project WHERE %s=%%s
                    """ % (self.resource_name, self.resource_name), (n,))

    def add(self, name, id_projects):
        """Link name with one or more id_project.

        :param name: name of the item (version, milestone, component)
        :param id_projects: a single project id or a list of project ids

        For each project id insert a row into the db. The table name is
        constructed from self.resource_name.

        """
        if not id_projects:
            return

        if not isinstance(id_projects, (list, tuple)):
            id_projects = [id_projects]

        with self.env.db_transaction as db:
            for id_proj in id_projects:
                db("""
                    INSERT INTO smp_%s_project (%s, id_project)
                    VALUES (%%s, %%s)
                    """ % (self.resource_name, self.resource_name),
                    (name, id_proj))

    def add_after_delete(self, name, id_projects):
        """Update data sets for item 'name' and the list of projects
        id_projects.

        @param name: the name of them item
        @param id_projects: single id of a project or list if ids

        Update is done by deleting the item from the SMP database and
        adding it again for the given projects. For each project a row
        is added to the table so inplace update won't work.

        This method is used when the set of projects an item
        (version, milestone, component) is associated with has changed.
        """
        self.delete(name)
        self.add(name, id_projects)

    def _get_all_names_and_project_id_for_resource(self, resource_name):
        return self.env.db_query("""
                SELECT %s, id_project FROM smp_%s_project
                """ % (resource_name, resource_name))

    def _update(self, resource_name, name, id_projects):

        self.env.db_transaction("""
            UPDATE smp_%s_project SET id_project=%%s WHERE %s=%%s
            """ % (resource_name, resource_name), (id_projects, name))

    def get_project_names_for_item(self, name):
        """Get a list of project names the item
        (version, milestone, component) is associated with.

        @param name: name of the item e.g. a component name
        @return: a list of project names
        """
        return [proj[0] for proj in self.env.db_query("""
                SELECT name FROM smp_project AS p, smp_%s_project AS res
                WHERE p.id_project=res.id_project AND res.%s=%%s
                """ % (self.resource_name, self.resource_name), (name,))]

    def get_project_ids_for_resource_item(self, resource_name, name):
        """Get a list of project ids the item of type resource_name is
        associated with.

        @param resource_name: may be any of component, version, milestone.
        @param name: name of the item e.g. a component name
        @return: a list of project ids
        """
        return [proj[0] for proj in self.env.db_query("""
                SELECT id_project FROM smp_%s_project
                WHERE %s=%%s ORDER BY id_project
                """ % (resource_name, resource_name), (name,))]

    def get_items_for_project_id(self, id_project):
        """Get all items associated with the given project id for a
        resource.

        :param id_project: a project id
        :return: a list of one or more items
        """
        return [item[0] for item in self.env.db_query("""
                SELECT %s FROM smp_%s_project
                WHERE id_project=%%s ORDER BY id_project
                """ % (self.resource_name, self.resource_name), (id_project,))]


class SmpComponent(SmpBaseModel):
    """Model for SMP components"""

    def __init__(self, env):
        super(SmpComponent, self).__init__(env)
        self.resource_name = "component"

    def get_all_components_and_project_id(self):
        """Get all components with associated project ids

        Note that a component may have several project ids and thus will
        be several times in the tuple.

        :return a list of tuples (component_name, project_id)
        """
        return self._get_all_names_and_project_id_for_resource('component')

    def get_components_for_project_id(self, id_project):
        """Get components for the given project id.

        :param id_project: a project id
        :return: ordered list of components associated with the given
                 project id. May be empty.
        """
        return self.get_items_for_project_id(id_project)


class SmpMilestone(SmpBaseModel):
    def __init__(self, env):
        super(SmpMilestone, self).__init__(env)
        self.resource_name = "milestone"

    def get_all_milestones_and_id_project_id(self):
        """Get all milestones with associated project ids

        Note that a milestone may have several project ids and thus will
        be several times in the tuple.
        :return a list of tuples (milestone_name, project_id)
        """
        return self._get_all_names_and_project_id_for_resource('milestone')

    def get_milestones_for_project_id(self, id_project):
        """Get milestones for the given project id.

        :param id_project: a project id
        :return: ordered list of milestones associated with the given
                 project id. May be empty.
        """
        return self.get_items_for_project_id(id_project)


class SmpProject(SmpBaseModel):

    def __init__(self, env):
        super(SmpProject, self).__init__(env)
        # TODO: a call to get_all_projects is missing to fill the custom
        # ticket field. Make sure to look at #12393 when implementing

    def get_name_and_id(self):
        return sorted(self.env.db_query("""
                SELECT name, id_project FROM smp_project
                """), key=lambda k: k[0])

    def get_all_projects(self):
        projects = self.env.db_query("""
                SELECT id_project,name,summary,description,closed,restrict_to
                FROM smp_project ORDER BY name
                """)

        project_names = [r[1] for r in sorted(projects, key=lambda k: k[1])]
        self.env.config.set('ticket-custom', 'project.options',
                            '|'.join(project_names))

        return projects


def get_all_versions_without_project(env):
    """Return a list of all known versions (as unicode) not linked to a
    project.
    """
    trac_vers = Version.select(env)
    all_versions_and_ids = SmpVersion(env).get_all_versions_and_project_id()
    all_versions = [v for v, id_ in all_versions_and_ids]
    versions = set(v.name for v in trac_vers) - set(all_versions)
    return list(versions)


class SmpVersion(SmpBaseModel):

    def __init__(self, env):
        super(SmpVersion, self).__init__(env)
        self.resource_name = "version"

    def get_all_versions_and_project_id(self):
        """Get all versions with associated project id

        :return a list of tuples (version_name, project_id)
        """
        return self._get_all_names_and_project_id_for_resource('version')

    def update_project_id_for_version(self, version_name, id_project):
        """TODO: get rid of old model"""
        self._update('version', version_name, id_project)

    def get_versions_for_project_id(self, id_project):
        """Get versions for the given project id.

        :param id_project: a project id
        :return: ordered list of versions associated with the given project id.
                 May be empty.
        """
        return self.get_items_for_project_id(id_project)
