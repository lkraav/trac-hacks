# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Cinc
#
# License: 3-clause BSD
#
from simplemultiproject.smp_model import PERM_TEMPLATE
from trac.core import TracError
from trac.perm import PermissionSystem
from trac.resource import Resource, ResourceNotFound
try:
    from trac.resource import ResourceExistsError
except:
    # Trac 1.2 doesn't know that exception yet
    class ResourceExistsError(TracError):
        """Thrown when attempting to insert an existing resource."""
from trac.ticket.model import TicketSystem
from trac.util.text import empty
from trac.util.translation import _


def _null_to_empty(value):
    return value if value else empty


def _to_null(value):
    return value if value else None


def simplify_whitespace(name):
    """Strip spaces and remove duplicate spaces within names"""
    if name:
        return ' '.join(name.split())
    return name


class Project(object):

    realm = 'project'

    exists = property(lambda self: self.id is not None)

    @property
    def resource(self):
        return Resource(self.realm, self.name)

    def __init__(self, env, name=None):
        """Create a new `Project` instance. If `name` is specified
        and the project with `name` exists, the project will be
        retrieved from the database.

        :raises ResourceNotFound: if `name` is not `None` and project
                                  with `name` does not exist.
        """
        self.env = env
        self.id = self.name = self._old_name = self.summary = self.description = None
        self.closed = self.restricted = None

        if name:
            for id_project, name, summary, description, closed, restrict_to in self.env.db_query("""
                                SELECT id_project,name,summary,description,closed,restrict_to
                                FROM smp_project WHERE name=%s
                                """, (name,)):
                self.id = id_project
                self.name = self._old_name = name
                self.summary = _null_to_empty(description)
                self.description = _null_to_empty(description)
                self.closed = self.completed = closed
                self.restricted = restrict_to
                break
            else:
                raise ResourceNotFound(_("Project %(name)s does not exist.",
                                         name=name))

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.name)

    def refresh_ticket_custom_list(self):
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
        TicketSystem(self.env).reset_ticket_fields()

    def delete(self):
        """Delete the project.

       :raises TracError: if project does not exist.
        """
        self.env.log.info("Deleting project '%s'", self.name)
        if not self.exists:
            raise TracError(_("Cannot delete non-existent project."))

        with self.env.db_transaction as db:
            for res in ('component', 'milestone', 'version'):
                db("""DELETE FROM smp_%s_project WHERE id_project=%%s""" % res, (self.id,))
            db("""DELETE FROM smp_project WHERE id_project=%s""", (self.id,))

        # remove permission from user
        permsys = PermissionSystem(self.env)
        permission = PERM_TEMPLATE % self.id
        users = permsys.get_users_with_permission(permission)
        for user in users:
            permsys.revoke_permission(user, permission)

        self.id = None
        # keep internal ticket custom field data up to date
        self.refresh_ticket_custom_list()

    def insert(self):
        """Insert a new project.

        Note that it is ok atm to have several projects with the same name.

        :raises TracError: if project name is empty.
        """
        if self.exists:
            raise ResourceExistsError(
                _('Project "%(name)s" already exists.', name=self.name))

        self.env.log.debug("Creating new project '%s'", self.name)
        self._check_and_coerce_fields()
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("""
                           INSERT INTO smp_project (name, summary, description, closed, restrict_to)
                           VALUES (%s,%s,%s,%s,%s)
                           """, (self.name, _to_null(self.summary),
                          _to_null(self.description), _to_null(self.closed),
                                 'YES' if self.restricted else None))
            self.id = db.get_last_id(cursor, 'smp_project', 'id_project')
        # keep internal ticket custom field data up to date
        self.refresh_ticket_custom_list()

    def update(self):
        """Update the project.

        :raises TracError: if project does not exist or project name
            is empty.
        :raises ResourceExistsError: if renamed project already exists.
        """
        if not self.exists:
            raise TracError(_("Cannot update non-existent project."))
        if not self.name:
            raise TracError(_("Invalid project name."))

        raise NotImplementedError

    @classmethod
    def select(cls, env):
        for prj in env.db_query("""
                SELECT id_project,name,summary,description,closed,restrict_to
                FROM smp_project ORDER BY name
                """):
            project = cls(env)
            project.id = prj[0]
            project.name = prj[1]
            project.summary = prj[2]
            project.description = prj[3]
            project.closed = prj[4]
            project.restricted = prj[5]
            yield project

    def _check_and_coerce_fields(self):
        self.name = simplify_whitespace(self.name)
        self.summary = simplify_whitespace(self.summary)
        self.description = simplify_whitespace(self.description)
        if not self.name:
            raise TracError(_("Invalid project name."))
