# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant

last_db_version = 1


class DownloadsInit(Component):
    """
       Init component initialises database and environment for downloads
       plugin.
    """
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        return self._get_db_version() != last_db_version

    def upgrade_environment(self, db):
        db_version = self._get_db_version()

        # Perform incremental upgrades
        for I in range(db_version + 1, last_db_version + 1):
            script_name = 'db%i' % I
            module = __import__('tracdownloads.db.%s' % script_name,
                                globals(), locals(), ['do_upgrade'])
            cursor = db.cursor()
            module.do_upgrade(self.env, cursor)

    def _get_db_version(self):
        for value, in self.env.db_query("""
                SELECT value FROM system WHERE name='downloads_version'
                """):
            return int(value)
        else:
            return 0
