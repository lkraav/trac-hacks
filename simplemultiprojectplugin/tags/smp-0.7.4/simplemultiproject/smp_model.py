# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#
from collections import namedtuple
from trac.perm import PermissionSystem
from trac.ticket.model import Version


__all__ = ['PERM_TEMPLATE', 'SmpMilestone', 'SmpComponent', 'SmpProject', 'SmpVersion']


PERM_TEMPLATE = u"PROJECT_%s_MEMBER"
Projecttuple = namedtuple('Projecttuple', ['id', 'name', 'summary', 'description', 'closed', 'restricted'])


class SmpBaseModel(object):
    """Base class for models providing the database access"""

    def __init__(self, env):
        self.env = env
        self.resource_name = "base"

    def delete(self, name):
        """Delete item 'name' from database table associating item and projects. Name may be a list or a
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

        @param name: the name of the item
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

    # Not used, because we had to keep different instances in sync
    # Each component holds a private instance atm
    _prj_cache = {}  # key: project name, value namedtuple with complete project info

    def __init__(self, env):
        super(SmpProject, self).__init__(env)
        # TODO: a call to get_all_projects is missing to fill the custom
        # ticket field. Make sure to look at #12393 when implementing

    # Not used atm
    def _update_cache(self, projects):
        self.prj_cache = {project.name: project for project in projects}

    def add(self, name, summary=None, description=None, closed=None, restrict_to=None):
        """Insert the given project into the table of know projects.

        Don't allow duplicate names here to prevent user confusion (the project IDis not visible to the user).

        :returns 0 on error, project_id as an integer otherwise
        """

        if self.project_exists(project_name=name):
            return 0

        prj_id = None
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""INSERT INTO smp_project (name, summary, description, closed, restrict_to)
                           VALUES(%s,%s,%s,%s,%s)""", (name , summary, description, closed, restrict_to))
            prj_id = db.get_last_id(cursor, 'smp_project', 'id_project')

        # keep internal ticket custom field data up to date
        self.get_all_projects()
        return prj_id

    def delete(self, prj_id):
        """Delete a project. This removes association for components, milestones and versions and removes
           user permissions if set"""
        if not prj_id:
            return

        if type(prj_id) is not list:
            prj_id = [prj_id]

        # remove permission from user
        permsys = PermissionSystem(self.env)
        for project_id in prj_id:
            permission = PERM_TEMPLATE % project_id
            users = permsys.get_users_with_permission(permission)
            for user in users:
                permsys.revoke_permission(user, permission)

        with self.env.db_transaction as db:
            for prj in prj_id:
                for res in ('component', 'milestone', 'version'):
                    db("""DELETE FROM smp_%s_project WHERE id_project=%%s""" % res, (prj,))
                db("""DELETE FROM smp_project WHERE id_project=%s""", (prj,))

        # keep internal ticket custom field data up to date
        self.get_all_projects()

    def _rename_project_in_ticket_custom_fields(self, old_name, name, db):
        """Change the project name in the ticket custom fields 'project' to a new name.

        Project information of tickets is held in a ticket custom field 'project'. When a project
        is renamed each ticket custom field for each affected ticket must be changed accordingly.
        """
        db("""UPDATE ticket_custom SET value='%s' WHERE name='project' AND value='%s'""" %
           (name, old_name))

    def update(self, prj_id, name, summary, desc, closed, restrict_to):
        if not prj_id:
            return

        with self.env.db_transaction as db:
            try:
                old_name = db("""SELECT name FROM smp_project WHERE id_project = %s""" %
                                         (prj_id, ))[0][0]
            except IndexError:
                return
            db("""UPDATE smp_project
                  SET name=%s, summary=%s, description=%s, closed=%s, restrict_to=%s
                  WHERE id_project=%s""", (name, summary, desc, closed, restrict_to, prj_id))
            if old_name != name:
                self._rename_project_in_ticket_custom_fields(old_name, name, db)
            self.get_all_projects()

    def get_name_and_id(self):
        return sorted(self.env.db_query("""
                SELECT name, id_project FROM smp_project
                """), key=lambda k: k[0])

    def get_all_projects(self):
        projects = self.env.db_query("""
                SELECT id_project,name,summary,description,closed,restrict_to
                FROM smp_project ORDER BY name
                """)
        project_names = [project[1] for project in projects]

        # TODO: Fix me. This only works sometimes. If the emmpty project name is already saved
        # in trac.ini, it will be loaded as default on startup and the 'ticket_without_project'
        # setting has no effect.
        #if self.env.config.getbool('simple-multi-project', 'ticket_without_project', False):

        # For now make tickets without projects the default
        project_names.append('')
        self.env.config.set('ticket-custom', 'project.options',
                            '|'.join(project_names))  # We don't save here. But see #12524

        return [Projecttuple(*prj) for prj in projects]
        # return [Project(prj[0], prj[1], prj[2], prj[3],None if not prj[4] else prj[4], prj[5]) for prj in projects]

    def project_exists(self, project_id=None, project_name=None):
        if not project_id and not project_name:
            return False

        if project_id:
            return self.env.db_query("""SELECT id_project FROM smp_project WHERE id_project = %s""" %
                                     (project_id, )) != []
        else:
            return self.env.db_query("""SELECT id_project FROM smp_project WHERE name = '%s'""" %
                                     (project_name, )) != []

    def apply_user_restrictions(self, projects, username=None, perms=None):
        """Create a new list of projects the user has access to.

        :param projects: list of projects. each item is a tuple with all known project informations
        :param username: name of the current user
        :param perms: PermissionCache object
        :return: a new filtered list of projects

        Filtering is done by checking if the user has permission PROJECT_<project_id>_MEMBER for any project
        in the project list.
        """
        if not perms:
            perms = PermissionSystem(self.env).get_user_permissions(username)

        # Note that the permission may be present but set to False
        return [prj for prj in projects if not prj.restricted or
                (PERM_TEMPLATE % prj.id in perms and perms[PERM_TEMPLATE % prj.id])]

    def get_project_from_ticket(self, tkt_id):
        # TODO: create usint test and rewrite as for loop
        projects = self.get_all_projects()
        prj_cache = {project.name: project for project in projects}

        for project_name in self.env.db_query("""SELECT value FROM ticket_custom
                                            WHERE name='project' AND ticket = %s""" % (tkt_id,)):
            name = project_name[0]
            try:
                return prj_cache[name]
            except KeyError:
                # Some old project name without a real project lingering in the ticket custom data for some reason.
                return None

        return None

    def get_project_from_name(self, name):
        # TODO: create usint test and rewrite as for loop
        projects = self.get_all_projects()
        prj_cache = {project.name: project for project in projects}

        try:
            return prj_cache[name]
        except KeyError:
            # Some old project name without a real project lingering in the ticket custom data for some reason.
            return None


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
        # TODO: this shouldn't be called with the resource name
        return self._get_all_names_and_project_id_for_resource('version')

    def get_versions_for_project_id(self, id_project):
        """Get versions for the given project id.

        :param id_project: a project id
        :return: ordered list of versions associated with the given project id.
                 May be empty.
        """
        return self.get_items_for_project_id(id_project)

    def get_project_ids_for_version(self, version_name):
        """Get a list of project ids his version is associated with

        :param version_name: name of a version
        :return: list of project ids
        """
        return self.get_project_ids_for_resource_item(self.resource_name, version_name)
