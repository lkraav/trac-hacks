# -*- coding: utf-8 -*-

from trac.core import Component, TracError, implements
from trac.db import *
from trac.env import IEnvironmentSetupParticipant

# Current discussion database schema version.
schema_version = 5


class DiscussionInit(Component):
    """[main] Initialises database and environment for discussion storage."""

    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        # Provide a db handle. A prepared cursor could get out-of-scope.
        schema_ver = self._get_schema_version(db)
        if schema_ver == schema_version:
            return False
        elif schema_ver > schema_version:
            raise TracError("A newer plugin version has been installed "
                            "before, but downgrading is unsupported.")
        self.log.info("TracDiscussion database schema version is %d, "
                      "should be %d"  % (schema_ver, schema_version))
        return True

    def upgrade_environment(self, db):
        """Each schema version should have its own upgrade module, named
        upgrades/dbN.py, where 'N' is the version number (int).
        """
        schema_ver = self._get_schema_version(db)

        cursor = db.cursor()
        # Always perform incremental upgrades.
        for i in range(schema_ver + 1, schema_version + 1):
            script_name  = 'db%i' % i
            try:
                upgrades = __import__('tracdiscussion.db', globals(),
                                      locals(), [script_name])
                script = getattr(upgrades, script_name)
            except AttributeError:
                raise TracError("No upgrade module for version %(num)i "
                                "(%(version)s.py)", num=i, version=name)
            script.do_upgrade(self.env, cursor)

        self.log.info("Upgraded TracDiscussion db schema from version "
                      "%d to %d" % (schema_ver, schema_version))
        db.commit()

    # Internal methods

    def _get_schema_version(self, db=None):
        """Return the current schema version for this plugin."""
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='discussion_version'
        """)
        row = cursor.fetchone()
        return row and int(row[0]) or 0
