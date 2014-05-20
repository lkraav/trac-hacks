"""
DefaultTicketImage:
a plugin for Trac to store the default image in the database
http://trac.edgewall.org
"""

from componentdependencies import IRequireComponents
from imagetrac.image import ImageTrac
from trac.core import *
from trac.db import Table, Column, Index, DatabaseManager
from trac.env import IEnvironmentSetupParticipant
from tracsqlhelper import create_table
from tracsqlhelper import get_scalar
from tracsqlhelper import insert_update


class DefaultTicketImage(Component):
    """
    store the default ticket image in a database
    """

    implements(IEnvironmentSetupParticipant, IRequireComponents)

    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        dburi = self.config.get('trac', 'database')
        tables = self._get_tables(dburi, cursor)
        if 'default_image' in tables:
            return False
        return True

    def upgrade_environment(self, db):
        self.create_db()
        db.commit()

    ### method for IRequireComponents

    def requires(self):
        return [ ImageTrac ]

    ### internal methods

    def create_db(self):
        default_image = Table('default_image', key=('ticket',))[
            Column('ticket', type='int'),
            Column('image'),
        ]
        create_table(self.env, default_image)

    def default_image(self, ticket_id, size=None):
        image = get_scalar(self.env, "SELECT image FROM default_image WHERE ticket=%s" % ticket_id)
        imagetrac = ImageTrac(self.env)
        images = imagetrac.images(ticket_id)
        if image:
            if not size:
                size = 'default'
            if size in images[image]:
                return image

        # find an image that works
        for i in images:
            if size:
                if size in images[i]:
                    return i
            else:
                return i

    def set_default(self, ticket_id, image):
        insert_update(self.env, 'default_image', 'ticket', ticket_id, dict(image=image))

    def _get_tables(self, dburi, cursor):
        """Code from TracMigratePlugin by Jun Omae (see tracmigrate.admin)."""
        if dburi.startswith('sqlite:'):
            sql = """
                SELECT name
                  FROM sqlite_master
                 WHERE type='table'
                   AND NOT name='sqlite_sequence'
            """
        elif dburi.startswith('postgres:'):
            sql = """
                SELECT tablename
                  FROM pg_tables
                 WHERE schemaname = ANY (current_schemas(false))
            """
        elif dburi.startswith('mysql:'):
            sql = "SHOW TABLES"
        else:
            raise TracError('Unsupported database type "%s"'
                            % dburi.split(':')[0])
        cursor.execute(sql)
        return sorted([row[0] for row in cursor])
